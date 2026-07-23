#include <ap_int.h>
#include <ap_axi_sdata.h>
#include <hls_stream.h>

// 8 feature EyeFeature HLS IP

#ifndef MAX_FRAME_W
#define MAX_FRAME_W 640
#endif

#ifndef MAX_FRAME_H
#define MAX_FRAME_H 640
#endif

#ifndef MAX_CENTER_W
#define MAX_CENTER_W 128
#endif
#ifndef MAX_CENTER_H
#define MAX_CENTER_H 64
#endif

#define INNER_X0_NUM 10
#define INNER_X1_NUM 90
#define INNER_Y0_NUM 18
#define INNER_Y1_NUM 88
#define INNER_DEN    100

#define HIST_BINS    64
#define HIST_SHIFT   2
#define LOW_PCT_DEFAULT  10
#define HIGH_PCT_DEFAULT 60
#define MIN_CONTRAST     12

typedef ap_axiu<32, 0, 0, 0> axis_word_t;

struct EyeCfg {
    bool valid;
    int cx0;
    int cy0;
    int cw;
    int ch;
};

struct EyeStats {
    bool valid;
    int ch;
    int cw;
    int max_run_low;
    int topk_sum_high;
    int topk_k;
    int dark_count_high;
    int row_run_high;
    int t_low;
    int t_high;
};

static int clamp_int(int v, int lo, int hi) {
#pragma HLS INLINE
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

static int abs_int(int v) {
#pragma HLS INLINE
    return (v < 0) ? -v : v;
}

static int round_ratio(int value, int num, int den) {
#pragma HLS INLINE
    return (value * num + den / 2) / den;
}

static int div_round_pos(int num, int den) {
#pragma HLS INLINE
    if (den <= 0) return 0;
    return (num + den / 2) / den;
}

static ap_uint<8> expand5(ap_uint<5> v) {
#pragma HLS INLINE
    ap_uint<8> vv = v;
    return (vv << 3) | (vv >> 2);
}

static ap_uint<8> expand6(ap_uint<6> v) {
#pragma HLS INLINE
    ap_uint<8> vv = v;
    return (vv << 2) | (vv >> 4);
}

static ap_uint<8> weighted_gray(ap_uint<8> r, ap_uint<8> g, ap_uint<8> b) {
#pragma HLS INLINE
    ap_uint<18> y = (ap_uint<18>)77 * r + (ap_uint<18>)150 * g + (ap_uint<18>)29 * b + 128;
    return (ap_uint<8>)(y >> 8);
}

static ap_uint<8> pixel_to_gray(ap_uint<32> data, int pixel_format) {
#pragma HLS INLINE
    if (pixel_format == 1 || pixel_format == 3) {
        ap_uint<8> r_field = expand5(data.range(15, 11));
        ap_uint<8> g_field = expand6(data.range(10, 5));
        ap_uint<8> b_field = expand5(data.range(4, 0));
        if (pixel_format == 3) {
            return weighted_gray(g_field, r_field, b_field);
        }
        return weighted_gray(r_field, g_field, b_field);
    } else if (pixel_format == 2) {
        ap_uint<8> r = data.range(23, 16);
        ap_uint<8> g = data.range(15, 8);
        ap_uint<8> b = data.range(7, 0);
        return weighted_gray(r, g, b);
    } else {
        return data.range(7, 0);
    }
}

static int sanitize_low_percent(int v) {
#pragma HLS INLINE
    if (v >= 1 && v <= 40) return v;
    return LOW_PCT_DEFAULT;
}

static int sanitize_high_percent(int v, int low_pct) {
#pragma HLS INLINE
    if (v > low_pct && v <= 95) return v;
    int fallback = low_pct + 50;
    if (fallback < HIGH_PCT_DEFAULT) fallback = HIGH_PCT_DEFAULT;
    if (fallback > 90) fallback = 90;
    return fallback;
}

static void robust_percent_params(int fixed_thresh, int adapt_offset, int &low_pct, int &high_pct) {
#pragma HLS INLINE
    if (fixed_thresh == 70 && adapt_offset == 25) {
        low_pct = LOW_PCT_DEFAULT;
        high_pct = HIGH_PCT_DEFAULT;
    } else {
        low_pct = sanitize_low_percent(fixed_thresh);
        high_pct = sanitize_high_percent(adapt_offset, low_pct);
    }
}

static EyeCfg make_eye_cfg(int frame_width, int frame_height, int x, int y, int w, int h) {
#pragma HLS INLINE
    EyeCfg c;
    c.valid = false;
    c.cx0 = 0;
    c.cy0 = 0;
    c.cw = 0;
    c.ch = 0;

    if (frame_width <= 0 || frame_height <= 0 || w <= 0 || h <= 0) return c;

    int rx0 = clamp_int(x, 0, frame_width - 1);
    int ry0 = clamp_int(y, 0, frame_height - 1);
    int rx1 = clamp_int(x + w, rx0 + 1, frame_width);
    int ry1 = clamp_int(y + h, ry0 + 1, frame_height);
    int rw = rx1 - rx0;
    int rh = ry1 - ry0;

    int ix0 = round_ratio(rw, INNER_X0_NUM, INNER_DEN);
    int ix1 = round_ratio(rw, INNER_X1_NUM, INNER_DEN);
    int iy0 = round_ratio(rh, INNER_Y0_NUM, INNER_DEN);
    int iy1 = round_ratio(rh, INNER_Y1_NUM, INNER_DEN);

    ix0 = clamp_int(ix0, 0, rw - 1);
    ix1 = clamp_int(ix1, ix0 + 1, rw);
    iy0 = clamp_int(iy0, 0, rh - 1);
    iy1 = clamp_int(iy1, iy0 + 1, rh);

    int cw = ix1 - ix0;
    int ch = iy1 - iy0;
    if (cw <= 0 || ch <= 0 || cw > MAX_CENTER_W || ch > MAX_CENTER_H) return c;

    c.valid = true;
    c.cx0 = rx0 + ix0;
    c.cy0 = ry0 + iy0;
    c.cw = cw;
    c.ch = ch;
    return c;
}

static int percentile_threshold(ap_uint<16> hist[HIST_BINS], int count, int percent) {
#pragma HLS INLINE off
    if (count <= 0) return 0;
    int target = div_round_pos(count * percent, 100);
    if (target < 1) target = 1;

    int selected = HIST_BINS - 1;
    int cumulative = 0;
    bool found = false;

    FIND_BIN:
    for (int i = 0; i < HIST_BINS; i++) {
#pragma HLS PIPELINE II=1
        if (!found) {
            cumulative += (int)hist[i];
            if (cumulative >= target) {
                selected = i;
                found = true;
            }
        }
    }
    int t = (selected << HIST_SHIFT) + ((1 << HIST_SHIFT) - 1);
    return clamp_int(t, 0, 255);
}

static int topk_sum_hist(ap_uint<16> runs[MAX_CENTER_W], int cw, int ch, int k) {
#pragma HLS INLINE off
    ap_uint<16> hist[MAX_CENTER_H + 1];
#pragma HLS ARRAY_PARTITION variable=hist cyclic factor=4 dim=1

    INIT_HIST:
    for (int i = 0; i <= MAX_CENTER_H; i++) {
#pragma HLS PIPELINE II=1
        hist[i] = 0;
    }

    BUILD_HIST:
    for (int x = 0; x < MAX_CENTER_W; x++) {
#pragma HLS PIPELINE II=1
        if (x < cw) {
            int r = (int)runs[x];
            if (r < 0) r = 0;
            if (r > ch) r = ch;
            hist[r] = hist[r] + 1;
        }
    }

    int remain = k;
    int sum = 0;
    ACCUM_TOPK:
    for (int h = MAX_CENTER_H; h >= 0; h--) {
#pragma HLS PIPELINE II=1
        if (h <= ch && remain > 0) {
            int cnt = (int)hist[h];
            int take = (cnt < remain) ? cnt : remain;
            sum += take * h;
            remain -= take;
        }
    }
    return sum;
}

static EyeStats compute_robust_stats(
    bool valid,
    int cw,
    int ch,
    ap_uint<8> pix_buf[MAX_CENTER_H][MAX_CENTER_W],
    ap_uint<16> gray_hist[HIST_BINS],
    int low_pct,
    int high_pct
) {
#pragma HLS INLINE off
    EyeStats st;
    st.valid = false;
    st.ch = ch;
    st.cw = cw;
    st.max_run_low = 0;
    st.topk_sum_high = 0;
    st.topk_k = 1;
    st.dark_count_high = 0;
    st.row_run_high = 0;
    st.t_low = 0;
    st.t_high = 0;
    if (!valid || cw <= 0 || ch <= 0 || cw > MAX_CENTER_W || ch > MAX_CENTER_H) return st;

    int count = cw * ch;
    int q_dark = percentile_threshold(gray_hist, count, low_pct);
    int q_ref = percentile_threshold(gray_hist, count, high_pct);
    if (q_ref < q_dark) q_ref = q_dark;
    int contrast = q_ref - q_dark;

    int t_low = q_dark;
    int t_high = q_dark;
    if (contrast >= MIN_CONTRAST) {
        t_low = q_dark + div_round_pos(contrast, 4);
        t_high = q_dark + div_round_pos(contrast, 2);
    }

    ap_uint<16> cur_low[MAX_CENTER_W];
    ap_uint<16> run_low[MAX_CENTER_W];
    ap_uint<16> cur_high[MAX_CENTER_W];
    ap_uint<16> run_high[MAX_CENTER_W];
#pragma HLS ARRAY_PARTITION variable=cur_low cyclic factor=4 dim=1
#pragma HLS ARRAY_PARTITION variable=run_low cyclic factor=4 dim=1
#pragma HLS ARRAY_PARTITION variable=cur_high cyclic factor=4 dim=1
#pragma HLS ARRAY_PARTITION variable=run_high cyclic factor=4 dim=1

    INIT_RUNS:
    for (int x = 0; x < MAX_CENTER_W; x++) {
#pragma HLS PIPELINE II=1
        cur_low[x] = 0;
        run_low[x] = 0;
        cur_high[x] = 0;
        run_high[x] = 0;
    }

    int dark_count_high = 0;
    int row_run_cur_high = 0;
    int row_run_best_high = 0;
    int min_dark_per_row = div_round_pos(cw, 10);
    if (min_dark_per_row < 1) min_dark_per_row = 1;

    ROBUST_ROWS:
    for (int y = 0; y < MAX_CENTER_H; y++) {
        if (y >= ch) break;
        int row_count_high = 0;
        ROBUST_COLS:
        for (int x = 0; x < MAX_CENTER_W; x++) {
#pragma HLS PIPELINE II=1
            if (x >= cw) break;
            int gray = (int)pix_buf[y][x];

            bool dark_low = (contrast >= MIN_CONTRAST) && (gray <= t_low);
            if (dark_low) {
                cur_low[x] = cur_low[x] + 1;
                if (cur_low[x] > run_low[x]) run_low[x] = cur_low[x];
            } else {
                cur_low[x] = 0;
            }

            bool dark_high = (contrast >= MIN_CONTRAST) && (gray <= t_high);
            if (dark_high) {
                cur_high[x] = cur_high[x] + 1;
                if (cur_high[x] > run_high[x]) run_high[x] = cur_high[x];
                dark_count_high++;
                row_count_high++;
            } else {
                cur_high[x] = 0;
            }
        }
        if (row_count_high >= min_dark_per_row) {
            row_run_cur_high++;
            if (row_run_cur_high > row_run_best_high) row_run_best_high = row_run_cur_high;
        } else {
            row_run_cur_high = 0;
        }
    }

    int max_low = 0;
    MAX_LOW:
    for (int x = 0; x < MAX_CENTER_W; x++) {
#pragma HLS PIPELINE II=1
        if (x < cw && (int)run_low[x] > max_low) max_low = (int)run_low[x];
    }

    int k = (cw + 3) / 4;
    if (k < 1) k = 1;
    int topk_high = topk_sum_hist(run_high, cw, ch, k);

    st.valid = true;
    st.ch = ch;
    st.cw = cw;
    st.max_run_low = max_low;
    st.topk_sum_high = topk_high;
    st.topk_k = k;
    st.dark_count_high = dark_count_high;
    st.row_run_high = row_run_best_high;
    st.t_low = t_low;
    st.t_high = t_high;
    return st;
}

static int eye_max_run_q(const EyeStats &a, int fixed_scale) {
#pragma HLS INLINE
    if (!a.valid || a.ch <= 0) return 0;
    return div_round_pos(a.max_run_low * fixed_scale, a.ch);
}

static int eye_topk_run_q(const EyeStats &a, int fixed_scale) {
#pragma HLS INLINE
    if (!a.valid || a.ch <= 0 || a.topk_k <= 0) return 0;
    int den = a.topk_k * a.ch;
    return div_round_pos(a.topk_sum_high * fixed_scale, den);
}

static int eye_dark_high_q(const EyeStats &a, int fixed_scale) {
#pragma HLS INLINE
    if (!a.valid || a.cw <= 0 || a.ch <= 0) return 0;
    return div_round_pos(a.dark_count_high * fixed_scale, a.cw * a.ch);
}

static int eye_row_run_high_q(const EyeStats &a, int fixed_scale) {
#pragma HLS INLINE
    if (!a.valid || a.ch <= 0) return 0;
    return div_round_pos(a.row_run_high * fixed_scale, a.ch);
}

static int combine_two_eyes(int qa, bool va, int qb, bool vb) {
#pragma HLS INLINE
    if (va && vb) return (qa + qb + 1) >> 1;
    if (va) return qa;
    if (vb) return qb;
    return 0;
}

static int diff_two_eyes(int qa, bool va, int qb, bool vb) {
#pragma HLS INLINE
    if (va && vb) return abs_int(qa - qb);
    return 0;
}

static int pack_debug(const EyeStats &left, const EyeStats &right) {
#pragma HLS INLINE
    int l = ((left.t_high & 0xFF) << 8) | (left.t_low & 0xFF);
    int r = ((right.t_high & 0xFF) << 8) | (right.t_low & 0xFF);
    return ((r & 0xFFFF) << 16) | (l & 0xFFFF);
}

static void write_out_word(hls::stream<axis_word_t> &out_stream, int value, bool last) {
#pragma HLS INLINE
    axis_word_t w;
    w.data = (ap_uint<32>)value;
    w.keep = 0xF;
    w.strb = 0xF;
    w.last = last ? 1 : 0;
    out_stream.write(w);
}

void eye_feature(
    hls::stream<axis_word_t> &in_stream,
    hls::stream<axis_word_t> &out_stream,
    int frame_width,
    int frame_height,
    int left_x,
    int left_y,
    int left_w,
    int left_h,
    int right_x,
    int right_y,
    int right_w,
    int right_h,
    int roi_valid,
    int fixed_thresh,
    int adapt_offset,
    int fixed_scale,
    int pixel_format,
    int roi_version
) {
#pragma HLS INTERFACE axis port=in_stream register_mode=both
#pragma HLS INTERFACE axis port=out_stream register_mode=both
#pragma HLS INTERFACE s_axilite port=frame_width bundle=CTRL
#pragma HLS INTERFACE s_axilite port=frame_height bundle=CTRL
#pragma HLS INTERFACE s_axilite port=left_x bundle=CTRL
#pragma HLS INTERFACE s_axilite port=left_y bundle=CTRL
#pragma HLS INTERFACE s_axilite port=left_w bundle=CTRL
#pragma HLS INTERFACE s_axilite port=left_h bundle=CTRL
#pragma HLS INTERFACE s_axilite port=right_x bundle=CTRL
#pragma HLS INTERFACE s_axilite port=right_y bundle=CTRL
#pragma HLS INTERFACE s_axilite port=right_w bundle=CTRL
#pragma HLS INTERFACE s_axilite port=right_h bundle=CTRL
#pragma HLS INTERFACE s_axilite port=roi_valid bundle=CTRL
#pragma HLS INTERFACE s_axilite port=fixed_thresh bundle=CTRL
#pragma HLS INTERFACE s_axilite port=adapt_offset bundle=CTRL
#pragma HLS INTERFACE s_axilite port=fixed_scale bundle=CTRL
#pragma HLS INTERFACE s_axilite port=pixel_format bundle=CTRL
#pragma HLS INTERFACE s_axilite port=roi_version bundle=CTRL
#pragma HLS INTERFACE s_axilite port=return bundle=CTRL

    if (fixed_scale <= 0) fixed_scale = 4096;

    int low_pct = LOW_PCT_DEFAULT;
    int high_pct = HIGH_PCT_DEFAULT;
    robust_percent_params(fixed_thresh, adapt_offset, low_pct, high_pct);

    bool global_valid = (roi_valid != 0) && frame_width > 0 && frame_height > 0 &&
                        frame_width <= MAX_FRAME_W && frame_height <= MAX_FRAME_H;

    EyeCfg eye0 = make_eye_cfg(frame_width, frame_height, left_x, left_y, left_w, left_h);
    EyeCfg eye1 = make_eye_cfg(frame_width, frame_height, right_x, right_y, right_w, right_h);
    if (!global_valid) {
        eye0.valid = false;
        eye1.valid = false;
    }

    static ap_uint<8> pix0[MAX_CENTER_H][MAX_CENTER_W];
    static ap_uint<8> pix1[MAX_CENTER_H][MAX_CENTER_W];
#pragma HLS BIND_STORAGE variable=pix0 type=ram_2p impl=bram
#pragma HLS BIND_STORAGE variable=pix1 type=ram_2p impl=bram

    ap_uint<16> hist0[HIST_BINS];
    ap_uint<16> hist1[HIST_BINS];
#pragma HLS ARRAY_PARTITION variable=hist0 cyclic factor=4 dim=1
#pragma HLS ARRAY_PARTITION variable=hist1 cyclic factor=4 dim=1

    INIT_HIST:
    for (int i = 0; i < HIST_BINS; i++) {
#pragma HLS PIPELINE II=1
        hist0[i] = 0;
        hist1[i] = 0;
    }

    FRAME_Y:
    for (int y = 0; y < MAX_FRAME_H; y++) {
        if (y >= frame_height) break;
        bool row0 = eye0.valid && (y >= eye0.cy0) && (y < eye0.cy0 + eye0.ch);
        bool row1 = eye1.valid && (y >= eye1.cy0) && (y < eye1.cy0 + eye1.ch);
        int ly0 = y - eye0.cy0;
        int ly1 = y - eye1.cy0;
        int ex0_0 = eye0.cx0;
        int ex0_1 = eye0.cx0 + eye0.cw;
        int ex1_0 = eye1.cx0;
        int ex1_1 = eye1.cx0 + eye1.cw;

        FRAME_X:
        for (int x = 0; x < MAX_FRAME_W; x++) {
#pragma HLS PIPELINE II=1
            if (x >= frame_width) break;
            axis_word_t inw = in_stream.read();
            ap_uint<8> gray = pixel_to_gray(inw.data, pixel_format);

            if (row0 && x >= ex0_0 && x < ex0_1) {
                int lx = x - eye0.cx0;
                pix0[ly0][lx] = gray;
                int bin = (int)(gray >> HIST_SHIFT);
                hist0[bin] = hist0[bin] + 1;
            }
            if (row1 && x >= ex1_0 && x < ex1_1) {
                int lx = x - eye1.cx0;
                pix1[ly1][lx] = gray;
                int bin = (int)(gray >> HIST_SHIFT);
                hist1[bin] = hist1[bin] + 1;
            }
        }
    }

    EyeStats st0 = compute_robust_stats(eye0.valid, eye0.cw, eye0.ch, pix0, hist0, low_pct, high_pct);
    EyeStats st1 = compute_robust_stats(eye1.valid, eye1.cw, eye1.ch, pix1, hist1, low_pct, high_pct);

    bool v0 = st0.valid;
    bool v1 = st1.valid;
    bool out_valid = v0 || v1;

    int f0_0 = eye_max_run_q(st0, fixed_scale);
    int f0_1 = eye_max_run_q(st1, fixed_scale);
    int f1_0 = eye_topk_run_q(st0, fixed_scale);
    int f1_1 = eye_topk_run_q(st1, fixed_scale);
    int dh_0 = eye_dark_high_q(st0, fixed_scale);
    int dh_1 = eye_dark_high_q(st1, fixed_scale);
    int rrh_0 = eye_row_run_high_q(st0, fixed_scale);
    int rrh_1 = eye_row_run_high_q(st1, fixed_scale);

    int avg_f0 = combine_two_eyes(f0_0, v0, f0_1, v1);
    int avg_f1 = combine_two_eyes(f1_0, v0, f1_1, v1);
    int avg_dark_high = combine_two_eyes(dh_0, v0, dh_1, v1);
    int avg_row_run_high = combine_two_eyes(rrh_0, v0, rrh_1, v1);
    int diff_f0 = diff_two_eyes(f0_0, v0, f0_1, v1);
    int diff_f1 = diff_two_eyes(f1_0, v0, f1_1, v1);
    int diff_dark_high = diff_two_eyes(dh_0, v0, dh_1, v1);
    int diff_row_run_high = diff_two_eyes(rrh_0, v0, rrh_1, v1);
    int debug_thresholds = pack_debug(st0, st1);

    if (!out_valid) {
        avg_f0 = 0;
        avg_f1 = 0;
        avg_dark_high = 0;
        avg_row_run_high = 0;
        diff_f0 = 0;
        diff_f1 = 0;
        diff_dark_high = 0;
        diff_row_run_high = 0;
        debug_thresholds = 0;
    }

    write_out_word(out_stream, avg_f0, false);
    write_out_word(out_stream, avg_f1, false);
    write_out_word(out_stream, avg_dark_high, false);
    write_out_word(out_stream, avg_row_run_high, false);
    write_out_word(out_stream, diff_f0, false);
    write_out_word(out_stream, diff_f1, false);
    write_out_word(out_stream, diff_dark_high, false);
    write_out_word(out_stream, diff_row_run_high, false);
    write_out_word(out_stream, out_valid ? 1 : 0, false);
    write_out_word(out_stream, roi_version, false);
    write_out_word(out_stream, debug_thresholds, true);
}
