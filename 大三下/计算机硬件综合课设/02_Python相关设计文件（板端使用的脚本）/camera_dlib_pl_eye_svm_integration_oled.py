# OV7670 + 异步 dlib ROI + PL EyeFeature + PL SVM 整体 PYNQ-Z1板端测试

import argparse
import csv
import os
import queue
import time
import multiprocessing as mp
from collections import deque
from pathlib import Path

import cv2
import numpy as np
from pynq import Overlay, MMIO, allocate
import pynq.pl_server.embedded_device  # Register Zynq embedded device in non-login SSH shells.

# 限制变量
AP_CTRL = 0x00

EYE_OFFSETS = {
    "frame_width":  0x10,
    "frame_height": 0x18,
    "left_x":       0x20,
    "left_y":       0x28,
    "left_w":       0x30,
    "left_h":       0x38,
    "right_x":      0x40,
    "right_y":      0x48,
    "right_w":      0x50,
    "right_h":      0x58,
    "roi_valid":    0x60,
    "fixed_thresh": 0x68,
    "adapt_offset": 0x70,
    "fixed_scale":  0x78,
    "pixel_format": 0x80,
    "roi_version":  0x88,
}

SVM_OFFSETS = {
    "threshold_q": 0x10,
}

EYE_OUTPUT_WORDS = 11
EYE_SVM_FEATURE_NAMES = (
    "avg_f0_q",
    "avg_f1_q",
    "avg_dark_high_q",
    "avg_row_run_high_q",
    "diff_f0_q",
    "diff_f1_q",
    "diff_dark_high_q",
    "diff_row_run_high_q",
)
SVM_INPUT_DIM = 120

# AXI VDMA S2MM 寄存器偏移
S2MM_DMACR = 0x30
S2MM_DMASR = 0x34
VDMA_PARK_PTR = 0x28
S2MM_VSIZE = 0xA0
S2MM_HSIZE = 0xA4
S2MM_FRMDLY_STRIDE = 0xA8
S2MM_START_ADDR_BASE = 0xAC

# AXI GPIO 通道偏移
GPIO_CH1_DATA = 0x00
GPIO_CH1_TRI = 0x04
GPIO_CH2_DATA = 0x08
GPIO_CH2_TRI = 0x0C


def log(msg):
    print(f"[CAM-DLIB-PL] {msg}", flush=True)


def try_set_affinity(cpu, name):
    if cpu is None or int(cpu) < 0:
        return
    try:
        os.sched_setaffinity(0, {int(cpu)})
        log(f"{name} pinned to CPU{int(cpu)}")
    except Exception as e:
        log(f"WARN: failed to pin {name} to CPU{cpu}: {e}")


def s32(x):
    x = int(x) & 0xFFFFFFFF
    if x & 0x80000000:
        x -= 0x100000000
    return x


def resolve_ip_name(ol, requested, aliases=()):
    keys = list(ol.ip_dict.keys())
    candidates = [requested] + list(aliases)
    for cand in candidates:
        cand = str(cand).strip()
        if not cand:
            continue
        variants = [cand, cand.lstrip("/")]
        for v in variants:
            if v in ol.ip_dict:
                return v
    lower_to_key = {k.lower(): k for k in keys}
    for cand in candidates:
        c = str(cand).strip().lstrip("/").lower()
        if c in lower_to_key:
            return lower_to_key[c]
    raise RuntimeError(f"IP '{requested}' not found. aliases={aliases}, available IPs={keys}")


def get_ip(ol, name, aliases=()):
    resolved = resolve_ip_name(ol, name, aliases)
    if hasattr(ol, resolved):
        return getattr(ol, resolved), resolved
    raise RuntimeError(f"Cannot access IP object '{resolved}'. ip_dict keys={list(ol.ip_dict.keys())}")


def get_ip_info(ol, name):
    resolved = resolve_ip_name(ol, name)
    return ol.ip_dict[resolved]


def int_auto(value):
    return int(str(value), 0)


class FatigueWindow:
    def __init__(self, window_sec, on_ratio, off_ratio, min_samples, score_threshold_q,
                 min_alert_sec, clear_open_sec):
        self.window_sec = max(1e-3, float(window_sec))
        self.on_ratio = float(on_ratio)
        self.off_ratio = float(off_ratio)
        self.min_samples = max(1, int(min_samples))
        self.score_threshold_q = int(score_threshold_q)
        self.min_alert_sec = max(0.0, float(min_alert_sec))
        self.clear_open_sec = max(0.0, float(clear_open_sec))
        self.samples = deque()
        self.active = False
        self.active_since = 0.0
        self.open_since = None

    def reset(self):
        self.samples.clear()
        self.active = False
        self.active_since = 0.0
        self.open_since = None

    def update(self, t_sec, svm_run, score_q):
        score_positive = -1
        if svm_run and int(score_q) != -2147483648:
            score_positive = 1 if int(score_q) > self.score_threshold_q else 0
            self.samples.append((float(t_sec), score_positive))
            if score_positive == 0:
                if self.open_since is None:
                    self.open_since = float(t_sec)
            else:
                self.open_since = None

        cutoff = float(t_sec) - self.window_sec
        while self.samples and self.samples[0][0] < cutoff:
            self.samples.popleft()

        sample_count = len(self.samples)
        positive_count = sum(v for _, v in self.samples)
        ratio = positive_count / sample_count if sample_count else 0.0
        event = ""

        if not self.active:
            if sample_count >= self.min_samples and ratio >= self.on_ratio:
                self.active = True
                self.active_since = float(t_sec)
                self.open_since = None
                event = "enter"
        else:
            open_clear = (
                self.clear_open_sec > 0.0
                and self.open_since is not None
                and (float(t_sec) - self.open_since) >= self.clear_open_sec
            )
            ratio_clear = (float(t_sec) - self.active_since) >= self.min_alert_sec and ratio <= self.off_ratio
            if open_clear or ratio_clear:
                self.active = False
                if open_clear:
                    event = "force_clear_open"
                    self.samples.clear()
                    sample_count = 0
                    positive_count = 0
                    ratio = 0.0
                else:
                    event = "clear"

        return {
            "score_positive": score_positive,
            "ratio": ratio,
            "samples": sample_count,
            "positive_count": positive_count,
            "active": int(self.active),
            "event": event,
        }


class AlertOutputs:
    def __init__(self, led_ip=None, tts_ip=None, led_offset=0, led_value=1,
                 tts_offset=0, tts_value=1, led_repeat_sec=3.25, tts_cooldown_sec=20.0):
        self.led_ip = led_ip
        self.tts_ip = tts_ip
        self.led_offset = int(led_offset)
        self.led_value = int(led_value)
        self.tts_offset = int(tts_offset)
        self.tts_value = int(tts_value)
        self.led_repeat_sec = max(0.2, float(led_repeat_sec))
        self.tts_cooldown_sec = max(0.2, float(tts_cooldown_sec))
        self.last_led_t = -1.0e9
        self.last_tts_t = -1.0e9

    def _write(self, ip, offset, value, label):
        if ip is None:
            return False
        try:
            ip.write(int(offset), int(value))
            return True
        except Exception as exc:
            log(f"WARN: failed to trigger {label}: {exc}")
            return False

    def update(self, t_sec, active, event):
        actions = []
        if not active:
            return ""
        if self.led_ip is not None and (event == "enter" or (float(t_sec) - self.last_led_t) >= self.led_repeat_sec):
            if self._write(self.led_ip, self.led_offset, self.led_value, "LED alert"):
                self.last_led_t = float(t_sec)
                actions.append("led")
        if self.tts_ip is not None and (event == "enter" or (float(t_sec) - self.last_tts_t) >= self.tts_cooldown_sec):
            if self._write(self.tts_ip, self.tts_offset, self.tts_value, "TTS alert"):
                self.last_tts_t = float(t_sec)
                actions.append("tts")
        return ",".join(actions)


def get_phys_addr(buf):
    if hasattr(buf, "physical_address"):
        return int(buf.physical_address)
    if hasattr(buf, "device_address"):
        return int(buf.device_address)
    raise RuntimeError("Cannot get physical/device address from PYNQ buffer")


def flush(buf):
    if hasattr(buf, "flush"):
        buf.flush()


def invalidate(buf):
    if hasattr(buf, "invalidate"):
        buf.invalidate()


def alloc_frame(shape, dtype):
    try:
        return allocate(shape=shape, dtype=dtype, cacheable=False)
    except TypeError:
        return allocate(shape=shape, dtype=dtype)


# GPIO VDMA
class CaptureGPIO:
    def __init__(self, ol, gpio_name, channel=1, bit=0):
        info = get_ip_info(ol, gpio_name)
        self.mmio = MMIO(info["phys_addr"], info["addr_range"])
        self.bit = int(bit)
        self.data_off = GPIO_CH1_DATA if int(channel) == 1 else GPIO_CH2_DATA
        self.tri_off = GPIO_CH1_TRI if int(channel) == 1 else GPIO_CH2_TRI
        log(f"GPIO {gpio_name}: base=0x{info['phys_addr']:08x}, ch={channel}, bit={bit}")
        self.mmio.write(self.tri_off, 0x00000000)

    def write_bit(self, value):
        cur = int(self.mmio.read(self.data_off))
        mask = 1 << self.bit
        if value:
            cur |= mask
        else:
            cur &= ~mask
        self.mmio.write(self.data_off, cur & 0xFFFFFFFF)

    def on(self):
        self.write_bit(1)

    def off(self):
        self.write_bit(0)


class VdmaS2MM:
    def __init__(self, ol, vdma_name, width, height, pixel_bytes=4, num_buffers=16, num_fstores=16):
        self.width = int(width)
        self.height = int(height)
        self.pixel_bytes = int(pixel_bytes)
        self.hsize = self.width * self.pixel_bytes
        self.stride = self.hsize
        self.vsize = self.height
        self.num_buffers = max(3, int(num_buffers))
        self.num_fstores = max(3, int(num_fstores))

        info = get_ip_info(ol, vdma_name)
        self.mmio = MMIO(info["phys_addr"], info["addr_range"])
        log(f"VDMA {vdma_name}: base=0x{info['phys_addr']:08x}, range=0x{info['addr_range']:x}")

        self.frames = [alloc_frame((self.height, self.width), np.uint32) for _ in range(self.num_buffers)]
        for f in self.frames:
            f[:] = 0
            flush(f)
        self.addrs = [get_phys_addr(f) for f in self.frames]
        log("Frame buffers: " + ", ".join(hex(a) for a in self.addrs))
        log(f"Program VDMA frame-store address registers: {self.num_fstores}")

    def read(self, off):
        return int(self.mmio.read(off))

    def write(self, off, value):
        self.mmio.write(off, int(value) & 0xFFFFFFFF)

    def status(self):
        cr = self.read(S2MM_DMACR)
        sr = self.read(S2MM_DMASR)
        park = self.read(VDMA_PARK_PTR)
        return cr, sr, park

    def status_str(self):
        cr, sr, park = self.status()
        return ("S2MM_DMACR=0x%08x S2MM_DMASR=0x%08x halted=%d idle=%d err=0x%03x PARK=0x%08x" %
                (cr, sr, sr & 1, (sr >> 1) & 1, (sr >> 4) & 0xFFF, park))

    def reset(self):
        self.write(S2MM_DMACR, 0x00000004)
        t0 = time.time()
        while time.time() - t0 < 1.0:
            if (self.read(S2MM_DMACR) & 0x4) == 0:
                break
            time.sleep(0.005)
        self.write(S2MM_DMASR, 0x0000FFFF)
        log("After VDMA reset: " + self.status_str())

    def start(self):
        self.reset()
        for i in range(self.num_fstores):
            self.write(S2MM_START_ADDR_BASE + 4 * i, self.addrs[i % self.num_buffers])
        self.write(S2MM_FRMDLY_STRIDE, self.stride)
        self.write(S2MM_HSIZE, self.hsize)
        self.write(S2MM_DMACR, 0x00000003)
        self.write(S2MM_VSIZE, self.vsize)
        time.sleep(0.05)
        log("After VDMA start: " + self.status_str())

    def stop(self):
        self.write(S2MM_DMACR, 0x00000000)
        time.sleep(0.05)
        log("After VDMA stop: " + self.status_str())

    def copy_frame565_into(self, buf_idx, dst_u16):
        src = self.frames[buf_idx % self.num_buffers]
        invalidate(src)
        dst_u16[:, :] = (np.asarray(src) & 0xFFFF).astype(np.uint16, copy=False)

    def free(self):
        for f in self.frames:
            try:
                f.freebuffer()
            except Exception:
                pass


# RGB565 / gray / dlib ROI
def unpack_rgb565(img565, byteswap=False):
    pix = img565.astype(np.uint16, copy=False)
    if byteswap:
        pix = (((pix & 0x00FF) << 8) | ((pix & 0xFF00) >> 8)).astype(np.uint16)
    r = ((pix >> 11) & 0x1F).astype(np.uint16) * 255 // 31
    g = ((pix >> 5) & 0x3F).astype(np.uint16) * 255 // 63
    b = (pix & 0x1F).astype(np.uint16) * 255 // 31
    return r.astype(np.uint8), g.astype(np.uint8), b.astype(np.uint8)


def rgb565_to_gray_fast(img565, color_mode="grb", byteswap=False):
    r, g, b = unpack_rgb565(img565, byteswap=byteswap)
    ch = {"r": r, "g": g, "b": b}
    mode = color_mode.lower()
    rr = ch[mode[0]].astype(np.uint16)
    gg = ch[mode[1]].astype(np.uint16)
    bb = ch[mode[2]].astype(np.uint16)
    return ((77 * rr + 150 * gg + 29 * bb) >> 8).astype(np.uint8)


def rgb565_to_bgr888(img565, color_mode="grb", byteswap=False):
    """Convert RGB565-like raw camera words to BGR888 for debug visualization."""
    r, g, b = unpack_rgb565(img565, byteswap=byteswap)
    ch = {"r": r, "g": g, "b": b}
    mode = color_mode.lower()
    if sorted(mode) != ["b", "g", "r"]:
        raise ValueError("color_mode must be one of rgb/rbg/grb/gbr/brg/bgr")
    rr, gg, bb = ch[mode[0]], ch[mode[1]], ch[mode[2]]
    return np.dstack((bb, gg, rr)).astype(np.uint8)


def rotate_flip_bgr(img_bgr, rotate="ccw", flip="none"):
    rotate = str(rotate).lower()
    if rotate == "cw":
        img_bgr = np.rot90(img_bgr, k=3)
    elif rotate == "ccw":
        img_bgr = np.rot90(img_bgr, k=1)
    elif rotate == "180":
        img_bgr = np.rot90(img_bgr, k=2)
    elif rotate in ("none", "0", ""):
        pass
    else:
        raise ValueError("rotate must be none/cw/ccw/180")

    flip = str(flip).lower()
    if flip == "h":
        img_bgr = np.fliplr(img_bgr)
    elif flip == "v":
        img_bgr = np.flipud(img_bgr)
    elif flip == "hv":
        img_bgr = np.flipud(np.fliplr(img_bgr))
    elif flip in ("none", ""):
        pass
    else:
        raise ValueError("flip must be none/h/v/hv")
    return np.ascontiguousarray(img_bgr)


def make_upright_bgr(img565, args):
    bgr = rgb565_to_bgr888(img565, color_mode=args.color_mode, byteswap=args.byteswap)
    return rotate_flip_bgr(bgr, rotate=args.rotate, flip=args.flip)


def select_raw_after_rotate_decimate(img565, rotate="ccw", decimate=2):
    dec = max(1, int(decimate))
    rot = str(rotate).lower()
    H, W = img565.shape[:2]
    if rot in ("none", "0", ""):
        out = img565[::dec, ::dec]
    elif rot == "180":
        out = img565[H - 1::-dec, W - 1::-dec]
    elif rot == "ccw":
        out = img565[::dec, W - 1::-dec].T
    elif rot == "cw":
        out = img565[H - 1::-dec, ::dec].T
    else:
        raise ValueError("rotate must be none/cw/ccw/180")
    return out


def apply_flip_2d(img, flip="none"):
    flip = str(flip).lower()
    if flip == "h":
        return np.fliplr(img)
    if flip == "v":
        return np.flipud(img)
    if flip == "hv":
        return np.flipud(np.fliplr(img))
    if flip in ("none", ""):
        return img
    raise ValueError("flip must be none/h/v/hv")


def make_dlib_gray_from_raw(img565, cfg):
    raw_small = select_raw_after_rotate_decimate(
        img565,
        rotate=cfg["rotate"],
        decimate=max(1, int(cfg["dlib_decimate"])),
    )
    raw_small = apply_flip_2d(raw_small, flip=cfg["flip"])
    gray = rgb565_to_gray_fast(raw_small, color_mode=cfg["color_mode"], byteswap=cfg["byteswap"])
    dlib_width = int(cfg.get("dlib_width", 0) or 0)
    if dlib_width > 0 and gray.shape[1] != dlib_width:
        scale = float(dlib_width) / float(gray.shape[1])
        new_h = max(1, int(round(gray.shape[0] * scale)))
        gray = cv2.resize(gray, (dlib_width, new_h), interpolation=cv2.INTER_AREA)
    return np.ascontiguousarray(gray)


def upright_dims(width, height, rotate):
    if str(rotate).lower() in ("cw", "ccw"):
        return int(height), int(width)
    return int(width), int(height)


def clamp_roi_dict(roi, W, H):
    if roi is None:
        return None
    x = int(round(roi["x"])); y = int(round(roi["y"]))
    w = int(round(roi["w"])); h = int(round(roi["h"]))
    x = max(0, min(x, W - 1)); y = max(0, min(y, H - 1))
    w = max(1, min(w, W - x)); h = max(1, min(h, H - y))
    return {"x": x, "y": y, "w": w, "h": h}


def clamp_roi(x, y, w, h, W, H):
    return clamp_roi_dict({"x": x, "y": y, "w": w, "h": h}, W, H)


def eye_roi_from_landmarks(shape, eye_indices, W, H, pad_x=0.35, pad_y=0.65):
    pts = [(shape.part(i).x, shape.part(i).y) for i in eye_indices]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    bw = max(1, x1 - x0 + 1)
    bh = max(1, y1 - y0 + 1)
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    rw = bw * (1.0 + 2.0 * pad_x)
    rh = bh * (1.0 + 2.0 * pad_y)
    return clamp_roi(cx - rw / 2.0, cy - rh / 2.0, rw, rh, W, H)


def detect_eye_rois(gray, detector, predictor, upsample=0):
    H, W = gray.shape[:2]
    faces = detector(gray, int(upsample))
    if len(faces) == 0:
        return None
    face = max(faces, key=lambda r: r.width() * r.height())
    shape = predictor(gray, face)
    left = eye_roi_from_landmarks(shape, range(36, 42), W, H)
    right = eye_roi_from_landmarks(shape, range(42, 48), W, H)
    face_box = {"x": face.left(), "y": face.top(), "w": face.width(), "h": face.height()}
    return face_box, left, right


def dlib_worker(req_q, res_q, shape_predictor_path, upsample, dlib_cpu, cfg):
    try_set_affinity(dlib_cpu, "dlib_worker")
    try:
        cv2.setNumThreads(1)
    except Exception:
        pass

    import dlib
    log("dlib_worker loading detector")
    detector = dlib.get_frontal_face_detector()
    log(f"dlib_worker loading predictor: {shape_predictor_path}")
    predictor = dlib.shape_predictor(shape_predictor_path)
    res_q.put({"type": "ready"})
    log("dlib_worker ready")

    while True:
        item = req_q.get()
        if item is None:
            log("dlib_worker exit")
            break
        frame_idx, t_sec, raw565 = item
        t_pre0 = time.perf_counter()
        gray = make_dlib_gray_from_raw(raw565, cfg)
        pre_ms = (time.perf_counter() - t_pre0) * 1000.0

        t_det0 = time.perf_counter()
        det = detect_eye_rois(gray, detector, predictor, upsample=upsample)
        det_ms = (time.perf_counter() - t_det0) * 1000.0
        total_ms = pre_ms + det_ms
        H, W = gray.shape[:2]

        if det is None:
            result = {
                "type": "result", "frame_idx": frame_idx, "t_sec": t_sec,
                "ok": 0, "face": None, "left": None, "right": None,
                "pre_ms": pre_ms, "dlib_ms": det_ms, "total_ms": total_ms,
                "dlib_w": W, "dlib_h": H,
            }
        else:
            face, left, right = det
            result = {
                "type": "result", "frame_idx": frame_idx, "t_sec": t_sec,
                "ok": 1, "face": face, "left": left, "right": right,
                "pre_ms": pre_ms, "dlib_ms": det_ms, "total_ms": total_ms,
                "dlib_w": W, "dlib_h": H,
            }
        try:
            while True:
                res_q.get_nowait()
        except queue.Empty:
            pass
        try:
            res_q.put_nowait(result)
        except queue.Full:
            pass


def scale_roi(roi, sx, sy):
    if roi is None:
        return None
    return {
        "x": int(round(roi["x"] * sx)),
        "y": int(round(roi["y"] * sy)),
        "w": int(round(roi["w"] * sx)),
        "h": int(round(roi["h"] * sy)),
    }


def smooth_roi(prev, cur, alpha):
    if cur is None:
        return None
    a = float(alpha)
    if prev is None or a <= 0.0:
        return dict(cur)
    if a >= 1.0:
        return dict(cur)
    out = {}
    for k in ("x", "y", "w", "h"):
        out[k] = int(round((1.0 - a) * int(prev[k]) + a * int(cur[k])))
    out["w"] = max(1, out["w"])
    out["h"] = max(1, out["h"])
    return out


def transform_point_upright_to_raw(xu, yu, raw_w, raw_h, rotate="ccw", flip="none"):
    """Map one point from post rotate+flip upright coordinates back to original raw VDMA coordinates."""
    rot = str(rotate).lower()
    flip = str(flip).lower()
    up_w, up_h = upright_dims(raw_w, raw_h, rot)

    # 翻转
    xr, yr = float(xu), float(yu)
    if "h" in flip:
        xr = (up_w - 1) - xr
    if "v" in flip:
        yr = (up_h - 1) - yr

    # 旋转
    if rot in ("none", "0", ""):
        x_raw, y_raw = xr, yr
    elif rot == "ccw":
        x_raw, y_raw = (raw_w - 1) - yr, xr
    elif rot == "cw":
        x_raw, y_raw = yr, (raw_h - 1) - xr
    elif rot == "180":
        x_raw, y_raw = (raw_w - 1) - xr, (raw_h - 1) - yr
    else:
        raise ValueError("rotate must be none/cw/ccw/180")
    return x_raw, y_raw


def upright_roi_to_raw_roi(roi, raw_w, raw_h, rotate="ccw", flip="none"):
    if roi is None:
        return None
    x0 = float(roi["x"])
    y0 = float(roi["y"])
    x1 = float(roi["x"] + max(1, roi["w"]) - 1)
    y1 = float(roi["y"] + max(1, roi["h"]) - 1)
    pts = [
        transform_point_upright_to_raw(x0, y0, raw_w, raw_h, rotate, flip),
        transform_point_upright_to_raw(x1, y0, raw_w, raw_h, rotate, flip),
        transform_point_upright_to_raw(x0, y1, raw_w, raw_h, rotate, flip),
        transform_point_upright_to_raw(x1, y1, raw_w, raw_h, rotate, flip),
    ]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x = int(round(min(xs)))
    y = int(round(min(ys)))
    w = int(round(max(xs) - min(xs) + 1))
    h = int(round(max(ys) - min(ys) + 1))
    return clamp_roi(x, y, w, h, raw_w, raw_h)


def transform_point_raw_to_upright(x_raw, y_raw, raw_w, raw_h, rotate="ccw", flip="none"):
    """Map one point from original raw VDMA coordinates to post rotate+flip upright coordinates."""
    rot = str(rotate).lower()
    flip = str(flip).lower()
    xr, yr = float(x_raw), float(y_raw)
    up_w, up_h = upright_dims(raw_w, raw_h, rot)

    # 旋转
    if rot in ("none", "0", ""):
        xu, yu = xr, yr
    elif rot == "ccw":
        xu, yu = yr, (raw_w - 1) - xr
    elif rot == "cw":
        xu, yu = (raw_h - 1) - yr, xr
    elif rot == "180":
        xu, yu = (raw_w - 1) - xr, (raw_h - 1) - yr
    else:
        raise ValueError("rotate must be none/cw/ccw/180")

    # 翻转
    if "h" in flip:
        xu = (up_w - 1) - xu
    if "v" in flip:
        yu = (up_h - 1) - yu
    return xu, yu


def raw_roi_to_upright_roi(roi, raw_w, raw_h, rotate="ccw", flip="none"):
    if roi is None:
        return None
    x0 = float(roi["x"])
    y0 = float(roi["y"])
    x1 = float(roi["x"] + max(1, roi["w"]) - 1)
    y1 = float(roi["y"] + max(1, roi["h"]) - 1)
    pts = [
        transform_point_raw_to_upright(x0, y0, raw_w, raw_h, rotate, flip),
        transform_point_raw_to_upright(x1, y0, raw_w, raw_h, rotate, flip),
        transform_point_raw_to_upright(x0, y1, raw_w, raw_h, rotate, flip),
        transform_point_raw_to_upright(x1, y1, raw_w, raw_h, rotate, flip),
    ]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    up_w, up_h = upright_dims(raw_w, raw_h, rotate)
    return clamp_roi(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, up_w, up_h)


def shrink_roi_for_eye_ip(roi, frame_w, frame_h, max_w=160, max_h=90):
    # 只弄一部分ROI区域
    if roi is None:
        return None, 0
    r = clamp_roi_dict(roi, frame_w, frame_h)
    x, y, w, h = r["x"], r["y"], r["w"], r["h"]
    new_w = w if int(max_w) <= 0 else min(w, int(max_w))
    new_h = h if int(max_h) <= 0 else min(h, int(max_h))
    if new_w == w and new_h == h:
        return r, 0
    cx = x + (w - 1) / 2.0
    cy = y + (h - 1) / 2.0
    shrunk = clamp_roi(cx - (new_w - 1) / 2.0, cy - (new_h - 1) / 2.0, new_w, new_h, frame_w, frame_h)
    return shrunk, 1


def make_upright_raw565_full(img565, rotate="ccw", flip="none"):
    raw = select_raw_after_rotate_decimate(img565, rotate=rotate, decimate=1)
    raw = apply_flip_2d(raw, flip=flip)
    return np.ascontiguousarray(raw)


# 输出debug视频
def auto_debug_video_path():
    ts = time.strftime("%Y%m%d_%H%M%S")
    return f"/home/xilinx/LC_SVM/outputs/runtime/camera_dlib_pl_debug_{ts}.avi"


def roi_from_row(row, prefix):
    x = int(row.get(f"{prefix}_x", -1))
    y = int(row.get(f"{prefix}_y", -1))
    w = int(row.get(f"{prefix}_w", -1))
    h = int(row.get(f"{prefix}_h", -1))
    if x < 0 or y < 0 or w <= 0 or h <= 0:
        return None
    return {"x": x, "y": y, "w": w, "h": h}


def draw_roi(img, roi, color, label="", thickness=2):
    if roi is None:
        return
    H, W = img.shape[:2]
    x = max(0, min(int(roi["x"]), W - 1))
    y = max(0, min(int(roi["y"]), H - 1))
    w = max(1, min(int(roi["w"]), W - x))
    h = max(1, min(int(roi["h"]), H - y))
    cv2.rectangle(img, (x, y), (x + w - 1, y + h - 1), color, thickness)
    if label:
        cv2.putText(img, label, (x, max(15, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)


def put_text_lines(img, lines, x=8, y=20, dy=17, font_scale=0.42):
    for i, line in enumerate(lines):
        yy = y + i * dy
        cv2.putText(img, line, (x, yy), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 2)
        cv2.putText(img, line, (x, yy), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1)


def draw_pred_badge(img, pred, svm_run, window_fill, window_len, score_q=None):
    H, W = img.shape[:2]
    if int(pred) == 1:
        label = "PRED CLOSED"
        color = (30, 30, 230)
    elif int(pred) == 0:
        label = "PRED OPEN"
        color = (30, 170, 40)
    else:
        label = "PRED WAIT"
        color = (90, 90, 90)

    if score_q is None or int(score_q) == -2147483648:
        sub = f"svm={int(svm_run)} win={int(window_fill)}/{int(window_len)}"
    else:
        sub = f"score={int(score_q)} win={int(window_fill)}/{int(window_len)}"
    x0 = 8
    y0 = max(8, H - 66)
    x1 = min(W - 8, x0 + 190)
    y1 = min(H - 8, y0 + 56)
    overlay = img.copy()
    cv2.rectangle(overlay, (x0, y0), (x1, y1), color, -1)
    cv2.addWeighted(overlay, 0.78, img, 0.22, 0, img)
    cv2.rectangle(img, (x0, y0), (x1, y1), (255, 255, 255), 1)
    cv2.putText(img, label, (x0 + 8, y0 + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
    cv2.putText(img, sub, (x0 + 8, y0 + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)


def draw_debug_frame(raw565, row, args):
    """Render one debug frame. Default view is upright, showing dlib ROI boxes."""
    view = str(args.debug_video_view).lower()
    if view == "raw":
        frame = rgb565_to_bgr888(raw565, color_mode=args.color_mode, byteswap=args.byteswap)
        left = roi_from_row(row, "left_eye")
        right = roi_from_row(row, "right_eye")
        face = None
        sent_left = None
        sent_right = None
        title = "RAW"
    else:
        frame = make_upright_bgr(raw565, args)
        left = roi_from_row(row, "left_upright")
        right = roi_from_row(row, "right_upright")
        face = roi_from_row(row, "face_upright")
        sent_left = roi_from_row(row, "left_sent_upright")
        sent_right = roi_from_row(row, "right_sent_upright")
        title = "UPRIGHT"

    roi_valid = int(row.get("roi_valid", 0)) == 1
    eye_valid = int(row.get("eye_valid", 0)) == 1
    draw_roi(frame, face, (255, 128, 0), "face", 1)
    draw_roi(frame, left, (0, 255, 0) if roi_valid else (0, 128, 255), "L", 2)
    draw_roi(frame, right, (0, 255, 0) if roi_valid else (0, 128, 255), "R", 2)
    if sent_left is not None or sent_right is not None:
        draw_roi(frame, sent_left, (255, 255, 0), "Ls", 1)
        draw_roi(frame, sent_right, (255, 255, 0), "Rs", 1)

    pred = int(row.get("svm_pred_post", row.get("svm_pred", -1)))
    score_q = int(row.get("svm_score_q", -2147483648))
    svm_run = int(row.get("svm_run", 0))
    window_fill = int(row.get("window_fill", 0))
    window_len = int(getattr(args, "window_len", 15))
    draw_pred_badge(frame, pred, svm_run, window_fill, window_len, score_q)

    lines = [
        f"{title} frame={int(row.get('frame_idx', -1))} fps={float(row.get('capture_fps_so_far', 0.0)):.2f} raw/post={int(row.get('svm_pred', -1))}/{pred} score={score_q}",
        f"fatigue={float(row.get('fatigue_ratio', 0.0)):.2f} samples={int(row.get('fatigue_samples', 0))} alert={int(row.get('fatigue_alert', 0))} actions={row.get('alert_actions', '')}",
        f"roi={int(row.get('roi_valid', 0))} age={int(row.get('roi_age', -1))} rv={int(row.get('roi_version', 0))} dlib={int(row.get('dlib_w', 0))}x{int(row.get('dlib_h', 0))}",
        f"eye={int(row.get('eye_run', 0))}/{int(row.get('eye_valid', 0))} avg=({int(row.get('eye_avg_f0_q', 0))},{int(row.get('eye_avg_f1_q', 0))},{int(row.get('eye_avg_dark_high_q', 0))},{int(row.get('eye_avg_row_run_high_q', 0))})",
        f"diff=({int(row.get('eye_diff_f0_q', 0))},{int(row.get('eye_diff_f1_q', 0))},{int(row.get('eye_diff_dark_high_q', 0))},{int(row.get('eye_diff_row_run_high_q', 0))})",
        f"L=({int(row.get('left_eye_x', -1))},{int(row.get('left_eye_y', -1))},{int(row.get('left_eye_w', -1))},{int(row.get('left_eye_h', -1))}) R=({int(row.get('right_eye_x', -1))},{int(row.get('right_eye_y', -1))},{int(row.get('right_eye_w', -1))},{int(row.get('right_eye_h', -1))})",
    ]
    if not eye_valid and int(row.get("eye_run", 0)):
        lines.append("WARN: EyeFeature ran but returned valid=0")
    put_text_lines(frame, lines)
    return frame


def write_debug_video(raw_frames, rows, args, actual_fps):
    if raw_frames is None or len(rows) == 0:
        return
    path = auto_debug_video_path() if args.save_debug_video == "auto" else args.save_debug_video
    if not path:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if args.save_debug_first_png:
        Path(args.save_debug_first_png).parent.mkdir(parents=True, exist_ok=True)
    if args.save_debug_last_png:
        Path(args.save_debug_last_png).parent.mkdir(parents=True, exist_ok=True)

    step = max(1, int(args.debug_video_every))
    indices = list(range(0, min(len(raw_frames), len(rows)), step))
    if not indices:
        return
    out_fps = float(args.debug_output_fps) if args.debug_output_fps > 0 else max(0.5, actual_fps / step)
    first = draw_debug_frame(raw_frames[indices[0]], rows[indices[0]], args)
    h0, w0 = first.shape[:2]
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*args.debug_fourcc), out_fps, (w0, h0))
    if not writer.isOpened():
        raise RuntimeError("Debug VideoWriter open failed. Try --debug-fourcc mp4v or output .avi with MJPG.")
    log(f"Writing debug video after capture: {path}, view={args.debug_video_view}, size={w0}x{h0}, fps={out_fps:.3f}, frames={len(indices)}")
    writer.write(first)
    if args.save_debug_first_png:
        cv2.imwrite(args.save_debug_first_png, first)
        log(f"Debug first PNG saved: {args.save_debug_first_png}")
    last = first
    for k, i in enumerate(indices[1:], start=2):
        last = draw_debug_frame(raw_frames[i], rows[i], args)
        writer.write(last)
        if k % max(1, int(round(out_fps))) == 0:
            log(f"writing debug video... {k}/{len(indices)}")
    writer.release()
    if args.save_debug_last_png:
        cv2.imwrite(args.save_debug_last_png, last)
        log(f"Debug last PNG saved: {args.save_debug_last_png}")
    log(f"Debug video saved: {path}")


# SVM系统DMA
def dma_status(ch):
    return int(ch._mmio.read(ch._offset + 0x04))


def wait_dma(ch, name, timeout=5.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = dma_status(ch)
        if st & 0x70:
            raise RuntimeError(f"{name} DMA error, DMASR=0x{st:08x}")
        if st & 0x02:
            return st
        time.sleep(0.001)
    raise TimeoutError(f"{name} timeout, DMASR=0x{dma_status(ch):08x}")


def write_eye_reg(ip, name, value):
    ip.write(EYE_OFFSETS[name], int(value))


def write_svm_reg(ip, name, value):
    ip.write(SVM_OFFSETS[name], int(value) & 0xFFFFFFFF)


def write_eye_config(ip, frame_w, frame_h, left, right, roi_valid, args, roi_version):
    if left is None:
        left = {"x": 0, "y": 0, "w": 1, "h": 1}
    if right is None:
        right = {"x": 0, "y": 0, "w": 1, "h": 1}

    write_eye_reg(ip, "frame_width", frame_w)
    write_eye_reg(ip, "frame_height", frame_h)
    write_eye_reg(ip, "left_x", left["x"])
    write_eye_reg(ip, "left_y", left["y"])
    write_eye_reg(ip, "left_w", left["w"])
    write_eye_reg(ip, "left_h", left["h"])
    write_eye_reg(ip, "right_x", right["x"])
    write_eye_reg(ip, "right_y", right["y"])
    write_eye_reg(ip, "right_w", right["w"])
    write_eye_reg(ip, "right_h", right["h"])
    write_eye_reg(ip, "roi_valid", int(roi_valid))
    write_eye_reg(ip, "fixed_thresh", args.fixed_thresh)
    write_eye_reg(ip, "adapt_offset", args.adapt_offset)
    write_eye_reg(ip, "fixed_scale", args.fixed_scale)
    write_eye_reg(ip, "pixel_format", args.eye_pixel_format)
    write_eye_reg(ip, "roi_version", int(roi_version))


def run_eye_full_frame_once(dma, ip, frame_words_u32, frame_w, frame_h, left, right, roi_valid, args, roi_version):
    """Send a full frame to EyeFeature IP. frame_words_u32 must be a flat uint32 array."""
    in_buf = allocate(shape=(frame_w * frame_h,), dtype=np.uint32)
    out_buf = allocate(shape=(EYE_OUTPUT_WORDS,), dtype=np.uint32)
    try:
        in_buf[:] = frame_words_u32.reshape(-1)
        out_buf[:] = 0
        flush(in_buf)
        flush(out_buf)

        write_eye_config(ip, frame_w, frame_h, left, right, roi_valid, args, roi_version)

        dma.recvchannel.transfer(out_buf)
        dma.sendchannel.transfer(in_buf)
        ip.write(AP_CTRL, 0x01)
        wait_dma(dma.sendchannel, "eye.send", args.timeout)
        wait_dma(dma.recvchannel, "eye.recv", args.timeout)
        invalidate(out_buf)
        raw = [int(x) for x in out_buf.tolist()]
        features = [s32(raw[i]) for i in range(len(EYE_SVM_FEATURE_NAMES))]
        return {
            "features_q": features,
            "avg_f0_q": features[0],
            "avg_f1_q": features[1],
            "avg_dark_high_q": features[2],
            "avg_row_run_high_q": features[3],
            "diff_f0_q": features[4],
            "diff_f1_q": features[5],
            "diff_dark_high_q": features[6],
            "diff_row_run_high_q": features[7],
            "feature0_q": features[0],
            "feature1_q": features[1],
            "valid": int(raw[8]),
            "roi_version": int(raw[9]),
            "debug": int(raw[10]),
            "raw": raw,
        }
    finally:
        in_buf.freebuffer()
        out_buf.freebuffer()


def run_svm_once(dma, ip, xq, timeout, threshold_q=0):
    xq_arr = np.asarray(xq, dtype=np.int32).reshape(-1)
    if xq_arr.size != SVM_INPUT_DIM:
        raise ValueError(f"SVM expects {SVM_INPUT_DIM} int32 words, got {xq_arr.size}")
    in_buf = allocate(shape=(SVM_INPUT_DIM,), dtype=np.int32)
    out_buf = allocate(shape=(2,), dtype=np.int32)
    try:
        in_buf[:] = xq_arr
        out_buf[:] = 0
        flush(in_buf)
        flush(out_buf)
        write_svm_reg(ip, "threshold_q", threshold_q)
        dma.recvchannel.transfer(out_buf)
        dma.sendchannel.transfer(in_buf)
        ip.write(AP_CTRL, 0x01)
        wait_dma(dma.sendchannel, "svm.send", timeout)
        wait_dma(dma.recvchannel, "svm.recv", timeout)
        invalidate(out_buf)
        return {
            "pred": int(out_buf[0]),
            "score_q": int(out_buf[1]),
            "raw": [int(out_buf[0]), int(out_buf[1])],
        }
    finally:
        in_buf.freebuffer()
        out_buf.freebuffer()


def build_svm_window_vector(feat_window, order: str) -> np.ndarray:
    # 给SVM组建窗口
    order = {
        "f0_then_f1": "feature_major",
        "f0_then_f1_newest_first": "feature_major_newest_first",
    }.get(order, order)
    frames = [tuple(int(v) for v in item) for item in feat_window]
    if any(len(item) != len(EYE_SVM_FEATURE_NAMES) for item in frames):
        raise ValueError(f"Each EyeFeature window item must have {len(EYE_SVM_FEATURE_NAMES)} values")

    if order == "feature_major":
        vals = [frames[t][k] for k in range(len(EYE_SVM_FEATURE_NAMES)) for t in range(len(frames))]
    elif order == "interleaved":
        vals = [frames[t][k] for t in range(len(frames)) for k in range(len(EYE_SVM_FEATURE_NAMES))]
    elif order == "feature_major_newest_first":
        vals = [frames[t][k] for k in range(len(EYE_SVM_FEATURE_NAMES)) for t in range(len(frames) - 1, -1, -1)]
    elif order == "interleaved_newest_first":
        vals = [frames[t][k] for t in range(len(frames) - 1, -1, -1) for k in range(len(EYE_SVM_FEATURE_NAMES))]
    else:
        raise ValueError(f"unknown window order: {order}")
    arr = np.asarray(vals, dtype=np.int32)
    if arr.size != SVM_INPUT_DIM:
        raise ValueError(f"SVM vector must be {SVM_INPUT_DIM}D, got {arr.size}")
    return arr


def frame_quick_hash(img565, step=32):
    s = img565[::step, ::step]
    return int(np.sum(s.astype(np.uint32)) & 0xFFFFFFFF)


def build_eye_input_frame(cur565, args):
    # 组建输入帧画面
    if args.eye_frame_orientation == "raw":
        frame565 = cur565
    elif args.eye_frame_orientation == "upright":
        frame565 = make_upright_raw565_full(cur565, rotate=args.rotate, flip=args.flip)
    else:
        raise ValueError("eye_frame_orientation must be raw/upright")

    frame_h, frame_w = frame565.shape[:2]
    if args.eye_pixel_format in (1, 3):
        return frame565.astype(np.uint32, copy=False), frame_w, frame_h
    if args.eye_pixel_format == 0:
        gray = rgb565_to_gray_fast(frame565, color_mode=args.color_mode, byteswap=args.byteswap)
        return gray.astype(np.uint32), frame_w, frame_h
    raise ValueError("This script currently supports --eye-pixel-format 0(gray), 1(RGB565), or 3(GRB565).")


def choose_eye_rois(left_upright, right_upright, args):
    """Choose ROI coordinate system according to the frame sent to EyeFeature."""
    if args.eye_frame_orientation == "upright":
        up_w, up_h = upright_dims(args.width, args.height, args.rotate)
        return clamp_roi_dict(left_upright, up_w, up_h), clamp_roi_dict(right_upright, up_w, up_h)
    # Default: PL sees original raw frame, so convert ROI back to raw VDMA coordinates.
    return (
        upright_roi_to_raw_roi(left_upright, args.width, args.height, args.rotate, args.flip),
        upright_roi_to_raw_roi(right_upright, args.width, args.height, args.rotate, args.flip),
    )


def main():
    try:
        cv2.setNumThreads(1)
    except Exception:
        pass

    p = argparse.ArgumentParser(description="Camera + async dlib ROI + PL EyeFeature + PL SVM integration 测试")
    p.add_argument("--bit", default="/home/xilinx/LC_SVM/final.bit")
    p.add_argument("--shape-predictor", default="/home/xilinx/LC_SVM/models/shape_predictor_68_face_landmarks.dat")

    p.add_argument("--vdma", default="axi_vdma_0")
    p.add_argument("--capture-gpio", default="axi_gpio_0")
    p.add_argument("--gpio-channel", type=int, default=1)
    p.add_argument("--gpio-bit", type=int, default=0)
    p.add_argument("--width", type=int, default=640)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--pixel-bytes", type=int, default=4)
    p.add_argument("--num-buffers", type=int, default=16)
    p.add_argument("--num-fstores", type=int, default=16)
    p.add_argument("--seconds", type=float, default=15.0)
    p.add_argument("--capture-fps", type=float, default=15.0)
    p.add_argument("--warmup", type=float, default=1.0)

    p.add_argument("--main-cpu", type=int, default=0)
    p.add_argument("--dlib-cpu", type=int, default=1)
    p.add_argument("--detect-interval", type=int, default=1)
    p.add_argument("--reuse-max-age", type=int, default=30)
    p.add_argument("--upsample", type=int, default=0)
    p.add_argument("--dlib-decimate", type=int, default=3)
    p.add_argument("--dlib-width", type=int, default=0)
    p.add_argument("--keep-latest-request", action="store_true", default=True)
    p.add_argument("--no-keep-latest-request", dest="keep_latest_request", action="store_false")

    p.add_argument("--color-mode", default="grb", choices=["rgb", "rbg", "grb", "gbr", "brg", "bgr"])
    p.add_argument("--byteswap", action="store_true")
    p.add_argument("--rotate", default="ccw", choices=["none", "cw", "ccw", "180"])
    p.add_argument("--flip", default="none", choices=["none", "h", "v", "hv"])

    p.add_argument("--eye-ip", default="eyefeature")
    p.add_argument("--eye-dma", default="eyefeature_dma")
    p.add_argument("--svm-ip", default="SVM")
    p.add_argument("--svm-dma", default="svm_dma")
    p.add_argument("--timeout", type=float, default=5.0)

    p.add_argument("--eye-frame-orientation", default="upright", choices=["raw", "upright"],
                   help="raw: send original VDMA full frame to EyeFeature and inverse-transform ROI; upright: rotate full frame before DMA")
    p.add_argument("--eye-pixel-format", type=int, default=3,
                   help="3=full GRB565 low16 words for current camera mode, 1=RGB565, 0=gray low8.")
    p.add_argument("--eye-roi-max-w", type=int, default=160,
                   help="Scheme-A PS-side ROI clamp before EyeFeature regs. 0 disables width clamp. HLS inner width is 80%% of this ROI, so 160 -> 128.")
    p.add_argument("--eye-roi-max-h", type=int, default=90,
                   help="Scheme-A PS-side ROI clamp before EyeFeature regs. 0 disables height clamp. HLS inner height is about 70%% of this ROI, so 90 -> about 63.")
    p.add_argument("--roi-smooth-alpha", type=float, default=0.0,
                   help="0 disables ROI smoothing. Try 0.25..0.45 to reduce dlib landmark/box jitter before EyeFeature.")
    p.add_argument("--fixed-thresh", type=int, default=10)
    p.add_argument("--adapt-offset", type=int, default=60)
    p.add_argument("--fixed-scale", type=int, default=4096)
    p.add_argument("--pl-interval", type=int, default=1,
                   help="Run EyeFeature/SVM every N captured frames. 1 means every frame.")
    p.add_argument("--skip-pl-until-roi", action="store_true", default=True)
    p.add_argument("--no-skip-pl-until-roi", dest="skip_pl_until_roi", action="store_false")
    p.add_argument("--window-len", type=int, default=15,
                   help="15 robust8 EyeFeature frames -> 120-D SVM vector")
    p.add_argument("--window-order", default="feature_major",
                   choices=["feature_major", "interleaved", "feature_major_newest_first", "interleaved_newest_first",
                            "f0_then_f1", "f0_then_f1_newest_first"],
                   help="120-D SVM layout. Correct default is feature_major: each of 8 features uses frame 0..14 oldest-to-newest.")
    p.add_argument("--dump-first-svm-vector", action="store_true",
                   help="Print the first 120-D vector sent to SVM for order verification.")
    p.add_argument("--svm-every", type=int, default=1,
                   help="Run SVM every N valid EyeFeature updates after the window is full")
    p.add_argument("--svm-threshold-q", type=int, default=0,
                   help="SVM IP threshold_q at AXI-Lite offset 0x10. Negative is more sensitive to CLOSED.")
    p.add_argument("--post-closed-hold", type=int, default=0,
                   help="Hold post-processed CLOSED for N frames after a raw CLOSED prediction. Raw svm_pred is still saved.")

    p.add_argument("--enable-fatigue-alert", action="store_true",
                   help="Enable sliding-window fatigue decision and trigger LED/TTS alerts.")
    p.add_argument("--fatigue-window-sec", type=float, default=30.0,
                   help="Sliding time window for fatigue ratio, based on valid SVM score samples.")
    p.add_argument("--fatigue-on-ratio", type=float, default=0.40,
                   help="Enter fatigue state when positive-score ratio reaches this value.")
    p.add_argument("--fatigue-off-ratio", type=float, default=0.20,
                   help="Leave fatigue state when positive-score ratio drops to this value.")
    p.add_argument("--fatigue-min-samples", type=int, default=60,
                   help="Minimum valid SVM score samples before fatigue can trigger.")
    p.add_argument("--fatigue-score-threshold-q", type=int, default=0,
                   help="Count a sample as closed/fatigue-positive when score_q is greater than this value.")
    p.add_argument("--alert-min-sec", type=float, default=3.0,
                   help="Minimum time to keep fatigue state active before allowing it to clear.")
    p.add_argument("--fatigue-clear-open-sec", type=float, default=4.0,
                   help="Force-clear fatigue alert after this many seconds of continuous non-positive score. 0 disables.")
    p.add_argument("--led-ip", default="GPIO_LED")
    p.add_argument("--led-offset", type=int_auto, default=0x00)
    p.add_argument("--led-alert-value", type=int_auto, default=1,
                   help="Value written to LED AXI reg0 bit0 path. Current IP treats bit0=1 as a red-light trigger.")
    p.add_argument("--led-repeat-sec", type=float, default=3.25,
                   help="Repeat LED trigger while fatigue remains active. LED hardware red duration is about 3s.")
    p.add_argument("--no-led-alert", action="store_true")
    p.add_argument("--tts-ip", default="UART_TTS")
    p.add_argument("--tts-offset", type=int_auto, default=0x00)
    p.add_argument("--tts-alert-value", type=int_auto, default=1,
                   help="Value written to TTS AXI reg0; any write to reg0 starts the fixed fatigue message.")
    p.add_argument("--tts-cooldown-sec", type=float, default=20.0,
                   help="Minimum interval between repeated TTS alerts while fatigue remains active.")
    p.add_argument("--no-tts-alert", action="store_true")

    p.add_argument("--enable-oled", action="store_true",
                   help="Enable low-rate OLED status display through the oled_spi_lite AXI-Lite IP.")
    p.add_argument("--oled-ip", default="SPI_SCREEN",
                   help="OLED SPI Lite IP instance name in the overlay hwh.")
    p.add_argument("--oled-controller", default="ssd1309", choices=["ssd1306", "ssd1309", "sh1106"],
                   help="OLED controller init sequence. The 2.42-inch 128x64 module is usually SSD1309-compatible.")
    p.add_argument("--oled-refresh-sec", type=float, default=1.0,
                   help="Minimum interval between OLED full-screen refreshes. Keep this >=0.5s to reduce CPU/MMIO cost.")
    p.add_argument("--oled-clk-div", type=int, default=5,
                   help="OLED SPI half-period divider inside oled_spi_lite. 5 is about 10 MHz with a 100 MHz AXI clock.")
    p.add_argument("--oled-required", action="store_true",
                   help="Raise an error if OLED initialization fails instead of continuing without the display.")
    p.add_argument("--enable-standby", action="store_true",
                   help="Enter light standby after a long no-face interval. EyeFeature/SVM/fatigue updates pause; dlib probes run at low rate.")
    p.add_argument("--standby-after-sec", type=float, default=10.0,
                   help="Enter standby after this many seconds without a detected face.")
    p.add_argument("--standby-probe-sec", type=float, default=5.0,
                   help="In standby, run one dlib face probe every N seconds.")

    p.add_argument("--out-csv", default="/home/xilinx/LC_SVM/outputs/runtime/camera_dlib_pl_eye_svm.csv")
    p.add_argument("--stream-csv", action="store_true",
                   help="Write CSV rows as they are produced instead of keeping all rows in memory.")
    p.add_argument("--csv-flush-every", type=int, default=30)
    p.add_argument("--save-debug-video", nargs="?", const="auto", default="",
                   help="Optional debug video path. Video is rendered after capture; default view marks dlib ROI boxes on upright frames.")
    p.add_argument("--debug-video-view", default="upright", choices=["upright", "raw"],
                   help="upright: draw dlib ROI in human-view frame; raw: draw ROI sent to EyeFeature on raw VDMA frame.")
    p.add_argument("--debug-video-every", type=int, default=1,
                   help="Save every Nth captured frame to debug video to reduce memory/output size.")
    p.add_argument("--debug-fourcc", default="MJPG")
    p.add_argument("--debug-output-fps", type=float, default=0.0,
                   help="0=use measured capture fps divided by --debug-video-every")
    p.add_argument("--save-debug-first-png", default="")
    p.add_argument("--save-debug-last-png", default="")
    p.add_argument("--print-every", type=int, default=1)
    p.add_argument("--no-hash", action="store_true")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--list-ips-only", action="store_true",
                   help="Load overlay, print resolved IP names, then exit without starting camera/dlib.")
    args = p.parse_args()

    if args.window_len * len(EYE_SVM_FEATURE_NAMES) != SVM_INPUT_DIM:
        raise ValueError(
            f"Current SVM path expects window_len={SVM_INPUT_DIM // len(EYE_SVM_FEATURE_NAMES)} because "
            f"EyeFeature returns {len(EYE_SVM_FEATURE_NAMES)} features per frame -> {SVM_INPUT_DIM}D."
        )
    if args.enable_fatigue_alert and args.fatigue_off_ratio > args.fatigue_on_ratio:
        raise ValueError("--fatigue-off-ratio should be <= --fatigue-on-ratio for hysteresis.")
    if args.enable_standby:
        args.standby_after_sec = max(1.0, float(args.standby_after_sec))
        args.standby_probe_sec = max(1.0, float(args.standby_probe_sec))
    stream_csv = bool(args.stream_csv or args.seconds <= 0)
    continuous_run = bool(args.seconds <= 0)
    if args.save_debug_video and stream_csv:
        raise ValueError("--save-debug-video cannot be combined with --stream-csv or --seconds <= 0, because debug video stores frames in RAM.")
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    if args.save_debug_video:
        dbg_path = auto_debug_video_path() if args.save_debug_video == "auto" else args.save_debug_video
        Path(dbg_path).parent.mkdir(parents=True, exist_ok=True)
    if args.save_debug_first_png:
        Path(args.save_debug_first_png).parent.mkdir(parents=True, exist_ok=True)
    if args.save_debug_last_png:
        Path(args.save_debug_last_png).parent.mkdir(parents=True, exist_ok=True)

    if args.list_ips_only:
        log(f"Loading overlay: {args.bit}")
        ol = Overlay(args.bit)
        log("IPs: " + ", ".join(ol.ip_dict.keys()))
        eye_name = resolve_ip_name(ol, args.eye_ip, aliases=("eye_feature", "eyefeature"))
        eye_dma_name = resolve_ip_name(ol, args.eye_dma, aliases=("eye_feature_dma",))
        svm_name = resolve_ip_name(ol, args.svm_ip, aliases=("svm", "SVM", "classify"))
        svm_dma_name = resolve_ip_name(ol, args.svm_dma, aliases=("SVM_dma",))
        log(f"Resolved EyeFeature IP={eye_name}, DMA={eye_dma_name}; SVM IP={svm_name}, DMA={svm_dma_name}")
        for name in (eye_name, eye_dma_name, svm_name, svm_dma_name):
            info = ol.ip_dict[name]
            log(f"{name}: phys=0x{int(info['phys_addr']):08x}, range=0x{int(info['addr_range']):x}, type={info.get('type', '')}")
        return

    try_set_affinity(args.main_cpu, "main_capture")

    worker_cfg = {
        "color_mode": args.color_mode,
        "byteswap": bool(args.byteswap),
        "rotate": args.rotate,
        "flip": args.flip,
        "dlib_decimate": int(args.dlib_decimate),
        "dlib_width": int(args.dlib_width),
    }
    req_q = mp.Queue(maxsize=1)
    res_q = mp.Queue(maxsize=2)
    worker = mp.Process(
        target=dlib_worker,
        args=(req_q, res_q, args.shape_predictor, args.upsample, args.dlib_cpu, worker_cfg),
        daemon=True,
    )
    worker.start()
    log("waiting for dlib worker")
    while True:
        msg = res_q.get()
        if isinstance(msg, dict) and msg.get("type") == "ready":
            break
    log("dlib worker ready")

    if continuous_run:
        expected_frames = 10**12
    else:
        expected_frames = int(np.ceil(args.seconds * args.capture_fps)) + 4
    tmp_frame = np.empty((args.height, args.width), dtype=np.uint16)
    raw_frames = None
    if args.save_debug_video:
        raw_frames = np.empty((expected_frames, args.height, args.width), dtype=np.uint16)
        log(f"Preallocated raw frames for debug video: {raw_frames.shape}, {raw_frames.nbytes/1024/1024:.1f} MiB")

    log(f"Loading overlay: {args.bit}")
    ol = Overlay(args.bit)
    log("IPs: " + ", ".join(ol.ip_dict.keys()))

    eye_dma, eye_dma_name = get_ip(ol, args.eye_dma, aliases=("eye_feature_dma",))
    eye_ip, eye_ip_name = get_ip(ol, args.eye_ip, aliases=("eye_feature", "eyefeature"))
    svm_dma, svm_dma_name = get_ip(ol, args.svm_dma, aliases=("SVM_dma",))
    svm_ip, svm_ip_name = get_ip(ol, args.svm_ip, aliases=("svm", "SVM", "classify"))
    log(f"Using EyeFeature IP={eye_ip_name}, DMA={eye_dma_name}; SVM IP={svm_ip_name}, DMA={svm_dma_name}")

    oled = None
    oled_last_t = -1.0e9
    oled_refresh_sec = max(0.1, float(args.oled_refresh_sec))
    if args.enable_oled:
        try:
            from pynq_oled_spi_lite import OledSpiLite

            oled_ip, oled_name = get_ip(
                ol,
                args.oled_ip,
                aliases=("SPI_SCREEN", "oled_spi_lite_0", "oled_spi_lite", "OLED_SCREEN"),
            )
            oled = OledSpiLite(
                oled_ip,
                controller=args.oled_controller,
                clk_div=args.oled_clk_div,
            )
            oled.init_display()
            oled.show_status(frame=0, fps=0.0, alert=False, score=0, ratio=0.0,
                             pred=-1, roi=0, eye=0, svm=0)
            oled_last_t = 0.0
            log(f"OLED enabled: IP={oled_name}, controller={args.oled_controller}, refresh={oled_refresh_sec:.2f}s")
        except Exception as exc:
            if args.oled_required:
                raise
            log(f"WARN: OLED disabled after init failure: {exc}")

    fatigue_window = None
    alert_outputs = None
    if args.enable_fatigue_alert:
        fatigue_window = FatigueWindow(
            window_sec=args.fatigue_window_sec,
            on_ratio=args.fatigue_on_ratio,
            off_ratio=args.fatigue_off_ratio,
            min_samples=args.fatigue_min_samples,
            score_threshold_q=args.fatigue_score_threshold_q,
            min_alert_sec=args.alert_min_sec,
            clear_open_sec=args.fatigue_clear_open_sec,
        )
        led_ip = None
        led_name = ""
        tts_ip = None
        tts_name = ""
        if not args.no_led_alert:
            led_ip, led_name = get_ip(ol, args.led_ip, aliases=("gpio_led", "GPIO_LED", "myip1", "myip1_0"))
        if not args.no_tts_alert:
            tts_ip, tts_name = get_ip(ol, args.tts_ip, aliases=("uart_tts", "UART_TTS", "TTS_HW", "TTS_HW_0"))
        alert_outputs = AlertOutputs(
            led_ip=led_ip,
            tts_ip=tts_ip,
            led_offset=args.led_offset,
            led_value=args.led_alert_value,
            tts_offset=args.tts_offset,
            tts_value=args.tts_alert_value,
            led_repeat_sec=args.led_repeat_sec,
            tts_cooldown_sec=args.tts_cooldown_sec,
        )
        log(
            "Fatigue alert enabled: "
            f"score>{args.fatigue_score_threshold_q}, window={args.fatigue_window_sec:.1f}s, "
            f"on/off={args.fatigue_on_ratio:.2f}/{args.fatigue_off_ratio:.2f}, "
            f"min_samples={args.fatigue_min_samples}, clear_open={args.fatigue_clear_open_sec:.1f}s, "
            f"LED={led_name or 'disabled'}, TTS={tts_name or 'disabled'}"
        )

    gpio = CaptureGPIO(ol, args.capture_gpio, channel=args.gpio_channel, bit=args.gpio_bit)
    vdma = VdmaS2MM(ol, args.vdma, args.width, args.height,
                    pixel_bytes=args.pixel_bytes,
                    num_buffers=args.num_buffers,
                    num_fstores=args.num_fstores)

    up_w, up_h = upright_dims(args.width, args.height, args.rotate)
    log(f"Dlib ROI coordinate frame after rotate/flip: upright {up_w}x{up_h}; EyeFeature frame={args.eye_frame_orientation}")
    log(f"Scheme-A ROI clamp before EyeFeature: max_w={args.eye_roi_max_w}, max_h={args.eye_roi_max_h} (0 disables a dimension)")

    rows = []
    hashes = []
    feat_window = deque(maxlen=args.window_len)

    n = 0
    req_sent = 0
    req_drop = 0
    res_recv = 0
    eye_runs = 0
    svm_runs = 0
    valid_feature_updates = 0

    last_pre_ms = 0.0
    last_dlib_ms = 0.0
    last_total_ms = 0.0
    last_dlib_frame = -1
    last_face = None
    last_left = None
    last_right = None
    smooth_face_upright = None
    smooth_left_upright = None
    smooth_right_upright = None
    last_roi_frame = -10**9
    roi_version = 0
    dlib_w = 0
    dlib_h = 0
    last_pred = -1
    last_post_pred = -1
    last_score_q = -2147483648
    closed_hold_left = 0
    last_eye = None
    dumped_first_svm_vector = False
    standby_active = False
    last_face_seen_t = 0.0
    last_standby_probe_t = -1.0e9
    no_face_sec = 0.0

    fieldnames = [
        "frame_idx", "t_sec", "capture_fps_so_far", "hash",
        "req_sent", "req_drop", "res_recv", "last_dlib_frame", "dlib_w", "dlib_h",
        "last_pre_ms", "last_dlib_ms", "last_total_ms",
        "roi_valid", "roi_age", "roi_version",
        "face_upright_x", "face_upright_y", "face_upright_w", "face_upright_h",
        "left_upright_x", "left_upright_y", "left_upright_w", "left_upright_h",
        "right_upright_x", "right_upright_y", "right_upright_w", "right_upright_h",
        "left_eye_pre_x", "left_eye_pre_y", "left_eye_pre_w", "left_eye_pre_h",
        "right_eye_pre_x", "right_eye_pre_y", "right_eye_pre_w", "right_eye_pre_h",
        "left_eye_x", "left_eye_y", "left_eye_w", "left_eye_h",
        "right_eye_x", "right_eye_y", "right_eye_w", "right_eye_h",
        "left_sent_upright_x", "left_sent_upright_y", "left_sent_upright_w", "left_sent_upright_h",
        "right_sent_upright_x", "right_sent_upright_y", "right_sent_upright_w", "right_sent_upright_h",
        "eye_roi_shrink",
        "eye_run", "eye_valid",
        "eye_avg_f0_q", "eye_avg_f1_q", "eye_avg_dark_high_q", "eye_avg_row_run_high_q",
        "eye_diff_f0_q", "eye_diff_f1_q", "eye_diff_dark_high_q", "eye_diff_row_run_high_q",
        "eye_feature0_q", "eye_feature1_q", "eye_out_roi_version", "eye_debug",
        "window_fill", "window_order", "svm_run", "svm_pred", "svm_pred_post",
        "svm_score_q", "svm_threshold_q", "closed_hold_left",
        "fatigue_score_positive", "fatigue_positive_count", "fatigue_samples",
        "fatigue_ratio", "fatigue_alert", "fatigue_event", "alert_actions",
        "standby_active", "no_face_sec",
        "vdma_status",
    ]

    csv_file = None
    csv_writer = None
    if stream_csv:
        csv_file = open(args.out_csv, "w", newline="", encoding="utf-8")
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_file.flush()
        log(f"Streaming CSV rows to: {args.out_csv}")

    try:
        gpio.off()
        log(f"Warmup: {args.warmup:.2f}s")
        time.sleep(max(0.0, args.warmup))

        vdma.start()
        gpio.on()
        time.sleep(0.5)

        sample_interval = 1.0 / max(0.1, float(args.capture_fps))
        t0 = time.perf_counter()
        next_sample = t0
        last_print_sec = -1
        log(
            "Capture + async dlib + PL EyeFeature/SVM: "
            f"seconds={'continuous' if continuous_run else f'{args.seconds:.2f}'}, target_fps={args.capture_fps:.2f}, "
            f"dlib_decimate={args.dlib_decimate}, detect_interval={args.detect_interval}, "
            f"eye_pixel_format={args.eye_pixel_format}, pl_interval={args.pl_interval}, "
            f"eye_roi_max=({args.eye_roi_max_w},{args.eye_roi_max_h}), "
            f"roi_smooth_alpha={args.roi_smooth_alpha:.2f}, svm_threshold_q={args.svm_threshold_q}, "
            f"post_closed_hold={args.post_closed_hold}, "
            f"window_order={args.window_order}, svm_dim={SVM_INPUT_DIM}, "
            f"standby={'on' if args.enable_standby else 'off'}"
            + (f"(after={args.standby_after_sec:.1f}s, probe={args.standby_probe_sec:.1f}s)" if args.enable_standby else "")
        )

        while True:
            now = time.perf_counter()
            elapsed = now - t0
            if (not continuous_run and elapsed >= args.seconds) or n >= expected_frames:
                break
            if now < next_sample:
                time.sleep(next_sample - now)

            now = time.perf_counter()
            elapsed = now - t0
            if (not continuous_run and elapsed >= args.seconds) or n >= expected_frames:
                break

            standby_event = ""

            # Drain newest dlib result if present.
            while True:
                try:
                    res = res_q.get_nowait()
                except queue.Empty:
                    break
                if not isinstance(res, dict) or res.get("type") != "result":
                    continue
                res_recv += 1
                last_pre_ms = float(res.get("pre_ms", 0.0))
                last_dlib_ms = float(res.get("dlib_ms", 0.0))
                last_total_ms = float(res.get("total_ms", 0.0))
                last_dlib_frame = int(res.get("frame_idx", -1))
                dlib_w = int(res.get("dlib_w", dlib_w))
                dlib_h = int(res.get("dlib_h", dlib_h))
                if int(res.get("ok", 0)):
                    last_face_seen_t = float(res.get("t_sec", elapsed))
                    if standby_active:
                        standby_active = False
                        standby_event = "exit"
                        feat_window.clear()
                        if fatigue_window is not None:
                            fatigue_window.reset()
                        closed_hold_left = 0
                        last_pred = -1
                        last_post_pred = -1
                        last_score_q = -2147483648
                        log("standby exit: face returned, resume EyeFeature/SVM")
                    last_face = res.get("face")
                    last_left = res.get("left")
                    last_right = res.get("right")
                    last_roi_frame = last_dlib_frame
                    roi_version += 1

            no_face_sec = max(0.0, elapsed - last_face_seen_t)
            if args.enable_standby and not standby_active and no_face_sec >= args.standby_after_sec:
                standby_active = True
                standby_event = "enter"
                last_standby_probe_t = elapsed
                last_face = None
                last_left = None
                last_right = None
                last_roi_frame = -10**9
                smooth_face_upright = None
                smooth_left_upright = None
                smooth_right_upright = None
                feat_window.clear()
                if fatigue_window is not None:
                    fatigue_window.reset()
                closed_hold_left = 0
                last_pred = -1
                last_post_pred = -1
                last_score_q = -2147483648
                log(f"standby enter: no face for {no_face_sec:.1f}s, pause EyeFeature/SVM")

            # Copy the full raw frame from VDMA DDR.
            buf_idx = n % vdma.num_buffers
            if raw_frames is not None:
                vdma.copy_frame565_into(buf_idx, raw_frames[n])
                cur565 = raw_frames[n]
            else:
                vdma.copy_frame565_into(buf_idx, tmp_frame)
                cur565 = tmp_frame

            h = -1 if args.no_hash else frame_quick_hash(cur565)
            if not args.no_hash:
                hashes.append(h)

            # Send only a COPY to dlib. In standby we probe much less often.
            send_dlib_request = False
            if standby_active:
                if (elapsed - last_standby_probe_t) >= args.standby_probe_sec:
                    send_dlib_request = True
                    last_standby_probe_t = elapsed
            elif n % max(1, int(args.detect_interval)) == 0:
                send_dlib_request = True

            if send_dlib_request:
                req_item = (n, elapsed, cur565.copy())
                try:
                    req_q.put_nowait(req_item)
                    req_sent += 1
                except queue.Full:
                    req_drop += 1
                    if args.keep_latest_request:
                        try:
                            req_q.get_nowait()
                        except Exception:
                            pass
                        try:
                            req_q.put_nowait(req_item)
                            req_sent += 1
                        except queue.Full:
                            pass

            roi_age = n - last_roi_frame
            roi_valid = int(last_left is not None and last_right is not None and roi_age <= int(args.reuse_max_age))

            # Scale dlib ROI to full upright frame first.
            sx = up_w / float(max(1, dlib_w))
            sy = up_h / float(max(1, dlib_h))
            face_upright_raw = scale_roi(last_face, sx, sy)
            left_upright_raw = scale_roi(last_left, sx, sy)
            right_upright_raw = scale_roi(last_right, sx, sy)
            if roi_valid:
                smooth_face_upright = smooth_roi(smooth_face_upright, face_upright_raw, args.roi_smooth_alpha)
                smooth_left_upright = smooth_roi(smooth_left_upright, left_upright_raw, args.roi_smooth_alpha)
                smooth_right_upright = smooth_roi(smooth_right_upright, right_upright_raw, args.roi_smooth_alpha)
                face_upright = smooth_face_upright
                left_upright = smooth_left_upright
                right_upright = smooth_right_upright
            else:
                smooth_face_upright = None
                smooth_left_upright = None
                smooth_right_upright = None
                face_upright = face_upright_raw
                left_upright = left_upright_raw
                right_upright = right_upright_raw
            left_eye_pre, right_eye_pre = choose_eye_rois(left_upright, right_upright, args)

            if args.eye_frame_orientation == "upright":
                eye_frame_w, eye_frame_h = up_w, up_h
            else:
                eye_frame_w, eye_frame_h = args.width, args.height
            left_eye, left_shrink = shrink_roi_for_eye_ip(
                left_eye_pre, eye_frame_w, eye_frame_h, args.eye_roi_max_w, args.eye_roi_max_h
            )
            right_eye, right_shrink = shrink_roi_for_eye_ip(
                right_eye_pre, eye_frame_w, eye_frame_h, args.eye_roi_max_w, args.eye_roi_max_h
            )
            eye_roi_shrink = int(left_shrink or right_shrink)

            if args.eye_frame_orientation == "raw":
                left_sent_upright = raw_roi_to_upright_roi(left_eye, args.width, args.height, args.rotate, args.flip)
                right_sent_upright = raw_roi_to_upright_roi(right_eye, args.width, args.height, args.rotate, args.flip)
            else:
                left_sent_upright = clamp_roi_dict(left_eye, up_w, up_h)
                right_sent_upright = clamp_roi_dict(right_eye, up_w, up_h)

            eye_run = 0
            svm_run = 0
            eye_valid = 0
            eye_features = [0] * len(EYE_SVM_FEATURE_NAMES)
            eye_f0 = 0
            eye_f1 = 0
            eye_out_roi_version = 0
            eye_debug = 0
            pred_this = -1
            pred_this_post = -1
            score_this_q = -2147483648

            if (not standby_active) and n % max(1, int(args.pl_interval)) == 0 and (roi_valid or not args.skip_pl_until_roi):
                frame_words, frame_w, frame_h = build_eye_input_frame(cur565, args)
                t_eye0 = time.perf_counter()
                last_eye = run_eye_full_frame_once(
                    eye_dma, eye_ip, frame_words, frame_w, frame_h,
                    left_eye, right_eye, roi_valid, args, roi_version,
                )
                eye_ms = (time.perf_counter() - t_eye0) * 1000.0
                eye_runs += 1
                eye_run = 1
                eye_valid = int(last_eye["valid"])
                eye_features = [int(v) for v in last_eye["features_q"]]
                eye_f0 = int(eye_features[0])
                eye_f1 = int(eye_features[1])
                eye_out_roi_version = int(last_eye["roi_version"])
                eye_debug = int(last_eye["debug"])

                if eye_valid and roi_valid:
                    feat_window.append(tuple(eye_features))
                    valid_feature_updates += 1
                    if len(feat_window) == args.window_len and valid_feature_updates % max(1, args.svm_every) == 0:
                        xq = build_svm_window_vector(feat_window, args.window_order)
                        if args.dump_first_svm_vector and not dumped_first_svm_vector:
                            log(f"first_svm_vector order={args.window_order}: {xq.tolist()}")
                            dumped_first_svm_vector = True
                        svm_res = run_svm_once(svm_dma, svm_ip, xq, args.timeout, args.svm_threshold_q)
                        pred_this = int(svm_res["pred"])
                        score_this_q = int(svm_res["score_q"])
                        last_pred = pred_this
                        last_score_q = score_this_q
                        if pred_this == 1:
                            closed_hold_left = max(0, int(args.post_closed_hold))
                            pred_this_post = 1
                        elif closed_hold_left > 0:
                            pred_this_post = 1
                            closed_hold_left -= 1
                        else:
                            pred_this_post = pred_this
                        last_post_pred = pred_this_post
                        svm_runs += 1
                        svm_run = 1
                if args.debug:
                    log(f"eye_ms={eye_ms:.2f}, eye={last_eye}, window={len(feat_window)}, svm_pred={pred_this}, score_q={score_this_q}")

            fatigue_info = {
                "score_positive": -1,
                "ratio": 0.0,
                "samples": 0,
                "positive_count": 0,
                "active": 0,
                "event": "",
            }
            alert_actions = ""
            if fatigue_window is not None and not standby_active:
                fatigue_info = fatigue_window.update(elapsed, svm_run, score_this_q)
                if alert_outputs is not None:
                    alert_actions = alert_outputs.update(
                        elapsed,
                        bool(fatigue_info["active"]),
                        str(fatigue_info["event"]),
                    )
                if fatigue_info["event"] or alert_actions:
                    log(
                        f"fatigue event={fatigue_info['event'] or '-'} active={fatigue_info['active']} "
                        f"ratio={fatigue_info['ratio']:.3f} samples={fatigue_info['samples']} "
                        f"pos={fatigue_info['positive_count']} actions={alert_actions or '-'}"
                    )

            actual_so_far = (n + 1) / max(1e-6, elapsed)
            row = {
                "frame_idx": n, "t_sec": elapsed, "capture_fps_so_far": actual_so_far, "hash": h,
                "req_sent": req_sent, "req_drop": req_drop, "res_recv": res_recv,
                "last_dlib_frame": last_dlib_frame, "dlib_w": dlib_w, "dlib_h": dlib_h,
                "last_pre_ms": last_pre_ms, "last_dlib_ms": last_dlib_ms, "last_total_ms": last_total_ms,
                "roi_valid": roi_valid, "roi_age": roi_age, "roi_version": roi_version,
                "face_upright_x": face_upright["x"] if face_upright else -1,
                "face_upright_y": face_upright["y"] if face_upright else -1,
                "face_upright_w": face_upright["w"] if face_upright else -1,
                "face_upright_h": face_upright["h"] if face_upright else -1,
                "left_upright_x": left_upright["x"] if left_upright else -1,
                "left_upright_y": left_upright["y"] if left_upright else -1,
                "left_upright_w": left_upright["w"] if left_upright else -1,
                "left_upright_h": left_upright["h"] if left_upright else -1,
                "right_upright_x": right_upright["x"] if right_upright else -1,
                "right_upright_y": right_upright["y"] if right_upright else -1,
                "right_upright_w": right_upright["w"] if right_upright else -1,
                "right_upright_h": right_upright["h"] if right_upright else -1,
                "left_eye_pre_x": left_eye_pre["x"] if left_eye_pre else -1,
                "left_eye_pre_y": left_eye_pre["y"] if left_eye_pre else -1,
                "left_eye_pre_w": left_eye_pre["w"] if left_eye_pre else -1,
                "left_eye_pre_h": left_eye_pre["h"] if left_eye_pre else -1,
                "right_eye_pre_x": right_eye_pre["x"] if right_eye_pre else -1,
                "right_eye_pre_y": right_eye_pre["y"] if right_eye_pre else -1,
                "right_eye_pre_w": right_eye_pre["w"] if right_eye_pre else -1,
                "right_eye_pre_h": right_eye_pre["h"] if right_eye_pre else -1,
                "left_eye_x": left_eye["x"] if left_eye else -1,
                "left_eye_y": left_eye["y"] if left_eye else -1,
                "left_eye_w": left_eye["w"] if left_eye else -1,
                "left_eye_h": left_eye["h"] if left_eye else -1,
                "right_eye_x": right_eye["x"] if right_eye else -1,
                "right_eye_y": right_eye["y"] if right_eye else -1,
                "right_eye_w": right_eye["w"] if right_eye else -1,
                "right_eye_h": right_eye["h"] if right_eye else -1,
                "left_sent_upright_x": left_sent_upright["x"] if left_sent_upright else -1,
                "left_sent_upright_y": left_sent_upright["y"] if left_sent_upright else -1,
                "left_sent_upright_w": left_sent_upright["w"] if left_sent_upright else -1,
                "left_sent_upright_h": left_sent_upright["h"] if left_sent_upright else -1,
                "right_sent_upright_x": right_sent_upright["x"] if right_sent_upright else -1,
                "right_sent_upright_y": right_sent_upright["y"] if right_sent_upright else -1,
                "right_sent_upright_w": right_sent_upright["w"] if right_sent_upright else -1,
                "right_sent_upright_h": right_sent_upright["h"] if right_sent_upright else -1,
                "eye_roi_shrink": eye_roi_shrink,
                "eye_run": eye_run, "eye_valid": eye_valid,
                "eye_avg_f0_q": eye_features[0],
                "eye_avg_f1_q": eye_features[1],
                "eye_avg_dark_high_q": eye_features[2],
                "eye_avg_row_run_high_q": eye_features[3],
                "eye_diff_f0_q": eye_features[4],
                "eye_diff_f1_q": eye_features[5],
                "eye_diff_dark_high_q": eye_features[6],
                "eye_diff_row_run_high_q": eye_features[7],
                "eye_feature0_q": eye_f0, "eye_feature1_q": eye_f1, "eye_debug": eye_debug,
                "eye_out_roi_version": eye_out_roi_version,
                "window_fill": len(feat_window), "window_order": args.window_order,
                "svm_run": svm_run, "svm_pred": pred_this, "svm_pred_post": pred_this_post,
                "svm_score_q": score_this_q, "svm_threshold_q": int(args.svm_threshold_q),
                "closed_hold_left": closed_hold_left,
                "fatigue_score_positive": int(fatigue_info["score_positive"]),
                "fatigue_positive_count": int(fatigue_info["positive_count"]),
                "fatigue_samples": int(fatigue_info["samples"]),
                "fatigue_ratio": float(fatigue_info["ratio"]),
                "fatigue_alert": int(fatigue_info["active"]),
                "fatigue_event": str(fatigue_info["event"]),
                "alert_actions": alert_actions,
                "standby_active": int(standby_active),
                "no_face_sec": float(no_face_sec),
                "vdma_status": vdma.status_str(),
            }
            if oled is not None:
                oled_due = (elapsed - oled_last_t) >= oled_refresh_sec
                oled_event = bool(fatigue_info.get("event")) or bool(standby_event)
                if oled_due or oled_event:
                    try:
                        if standby_active:
                            until_probe = max(0.0, args.standby_probe_sec - (elapsed - last_standby_probe_t))
                            countdown = int(until_probe + 0.999)
                            oled.show_standby(countdown=countdown, no_face_sec=no_face_sec)
                        else:
                            display_score = score_this_q if svm_run else last_score_q
                            display_pred = pred_this_post if svm_run else last_post_pred
                            oled.show_status(
                                frame=n,
                                fps=actual_so_far,
                                alert=bool(fatigue_info["active"]),
                                score=display_score,
                                ratio=float(fatigue_info["ratio"]),
                                pred=display_pred,
                                roi=int(roi_valid),
                                eye=int(eye_valid),
                                svm=int(svm_run),
                            )
                        oled_last_t = elapsed
                    except Exception as exc:
                        log(f"WARN: OLED update failed, disabling display updates: {exc}")
                        oled = None
            if csv_writer is not None:
                csv_writer.writerow(row)
                if args.csv_flush_every <= 1 or n % max(1, int(args.csv_flush_every)) == 0 or alert_actions:
                    csv_file.flush()
            else:
                rows.append(row)

            if args.print_every > 0 and (n % args.print_every == 0 or svm_run):
                log(
                    f"frame={n:04d} fps={actual_so_far:.2f} "
                    f"roi={roi_valid} age={roi_age} rv={roi_version} "
                    f"eye_run={eye_run} eye_valid={eye_valid} avg=({eye_features[0]},{eye_features[1]},{eye_features[2]},{eye_features[3]}) "
                    f"diff=({eye_features[4]},{eye_features[5]},{eye_features[6]},{eye_features[7]}) "
                    f"roiH=({left_eye_pre['h'] if left_eye_pre else -1}->{left_eye['h'] if left_eye else -1},"
                    f"{right_eye_pre['h'] if right_eye_pre else -1}->{right_eye['h'] if right_eye else -1}) "
                    f"win={len(feat_window)}/{args.window_len} svm_run={svm_run} "
                    f"pred={pred_this if svm_run else last_pred}/{pred_this_post if svm_run else last_post_pred} "
                    f"score={score_this_q if svm_run else last_score_q} thr={args.svm_threshold_q} "
                    f"fat={fatigue_info['ratio']:.2f}/{fatigue_info['samples']} alert={fatigue_info['active']} "
                    f"standby={int(standby_active)} noface={no_face_sec:.1f} "
                    f"dlib_ms={last_dlib_ms:.1f} res={res_recv}"
                )
            else:
                sec = int(elapsed)
                if sec != last_print_sec:
                    last_print_sec = sec
                    log(
                        f"capturing... {sec}s frames={n+1} fps={actual_so_far:.2f} "
                        f"req={req_sent} drop={req_drop} res={res_recv} roi={roi_valid} "
                        f"eye_runs={eye_runs} svm_runs={svm_runs} last_pred={last_pred}/{last_post_pred} "
                        f"score={last_score_q} fat={fatigue_info['ratio']:.2f}/{fatigue_info['samples']} "
                        f"alert={fatigue_info['active']} standby={int(standby_active)} noface={no_face_sec:.1f}"
                    )

            n += 1
            next_sample += sample_interval
            if next_sample < time.perf_counter() - sample_interval:
                next_sample = time.perf_counter() + sample_interval

        real_elapsed = time.perf_counter() - t0
        gpio.off()
        time.sleep(0.05)
        vdma.stop()

        # Drain late dlib results for final stats only.
        t_drain = time.perf_counter()
        while time.perf_counter() - t_drain < 0.2:
            try:
                res = res_q.get_nowait()
            except queue.Empty:
                break
            if isinstance(res, dict) and res.get("type") == "result":
                res_recv += 1

        actual_fps = n / real_elapsed if real_elapsed > 0 else 0.0
        dlib_result_fps = res_recv / real_elapsed if real_elapsed > 0 else 0.0
        eye_fps = eye_runs / real_elapsed if real_elapsed > 0 else 0.0
        svm_fps = svm_runs / real_elapsed if real_elapsed > 0 else 0.0
        log(f"Done: elapsed={real_elapsed:.3f}s, frames={n}, capture_fps={actual_fps:.2f}")
        log(f"dlib req_sent={req_sent}, req_drop={req_drop}, results={res_recv}, result_fps={dlib_result_fps:.2f}")
        log(f"EyeFeature runs={eye_runs}, eye_fps={eye_fps:.2f}; SVM runs={svm_runs}, svm_fps={svm_fps:.2f}; last_pred={last_pred}/{last_post_pred}; last_score_q={last_score_q}")
        if hashes:
            log(f"Unique hashes: total={len(set(hashes))}/{len(hashes)}, recent={len(set(hashes[-20:]))}")

        if csv_writer is not None:
            csv_file.flush()
            log(f"CSV streamed: {args.out_csv}")
        else:
            with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)
            log(f"CSV saved: {args.out_csv}")

        if args.save_debug_video:
            write_debug_video(raw_frames[:n] if raw_frames is not None else None, rows, args, actual_fps)

    except KeyboardInterrupt:
        log("Interrupted by user.")

    finally:
        try:
            if csv_file is not None and not csv_file.closed:
                csv_file.close()
        except Exception:
            pass
        try:
            if "gpio" in locals():
                gpio.off()
        except Exception:
            pass
        try:
            if "vdma" in locals():
                vdma.stop()
        except Exception:
            pass
        try:
            req_q.put_nowait(None)
        except Exception:
            pass
        try:
            worker.join(timeout=2.0)
            if worker.is_alive():
                worker.terminate()
        except Exception:
            pass
        try:
            gpio.off()
        except Exception:
            pass
        try:
            vdma.stop()
        except Exception:
            pass
        try:
            vdma.free()
        except Exception:
            pass


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
