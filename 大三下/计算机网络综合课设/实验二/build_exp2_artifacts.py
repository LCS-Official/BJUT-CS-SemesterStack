from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "实验2截图"
PCAP = OUT / "exp2_mix.pcapng"
WS = ROOT / "WiresharkPortable64" / "App" / "Wireshark"
TSHARK = WS / "tshark.exe"
DUMPCAP = WS / "dumpcap.exe"
CAPINFOS = WS / "capinfos.exe"


def run(args):
    p = subprocess.run(
        [str(a) for a in args],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return p.stdout.strip() or f"(exit {p.returncode}, no stdout)"


def save_text(name, text):
    path = OUT / f"{name}.txt"
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def font(size):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap(draw, line, fnt, width):
    if not line:
        return [""]
    out, cur = [], ""
    for ch in line.expandtabs(4):
        nxt = cur + ch
        if draw.textlength(nxt, font=fnt) <= width or not cur:
            cur = nxt
        else:
            out.append(cur)
            cur = ch
    out.append(cur)
    return out


def render(name, title, text, max_lines=110):
    body_font = font(24)
    title_font = font(36)
    width, pad = 1800, 44
    dummy = Image.new("RGB", (width, 100), "white")
    draw = ImageDraw.Draw(dummy)
    lines = []
    for line in text.splitlines()[:max_lines]:
        lines.extend(wrap(draw, line, body_font, width - pad * 2))
    if len(text.splitlines()) > max_lines:
        lines.append(f"... 已省略，完整内容见 {name}.txt")
    line_h = 34
    height = pad + 52 + 28 + max(1, len(lines)) * line_h + pad
    img = Image.new("RGB", (width, height), "#fbfbf8")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, width, 88), fill="#253141")
    draw.text((pad, 22), title, font=title_font, fill="white")
    y = 112
    for line in lines:
        draw.text((pad, y), line, font=body_font, fill="#111827")
        y += line_h
    img.save(OUT / f"{name}.png")


def make(name, title, text, max_lines=110):
    save_text(name, text)
    render(name, title, text, max_lines)


OUT.mkdir(exist_ok=True)

for filename, filt in {
    "filter_arp.pcapng": "arp",
    "filter_icmp.pcapng": "icmp",
    "filter_tcp_ipv4.pcapng": "tcp and ip",
    "filter_udp_dns.pcapng": "udp or dns",
}.items():
    subprocess.run(
        [str(TSHARK), "-r", str(PCAP), "-Y", filt, "-w", str(OUT / filename)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

network = "\n\n".join(
    [
        "=== ipconfig /all ===",
        run(["ipconfig", "/all"]),
        "=== route print -4 ===",
        run(["route", "print", "-4"]),
        "=== arp -a ===",
        run(["arp", "-a"]),
    ]
)
make("01_网络配置", "实验2 网络配置截图", network, 95)

interfaces = "\n".join(
    [
        "Wireshark/Dumpcap 接口列表：",
        run([DUMPCAP, "-D"]),
        "",
        "本次抓包接口：5. WLAN",
        "抓包命令：dumpcap -i 5 -a duration:25 -w 实验2截图\\exp2_mix.pcapng",
        "混杂模式：dumpcap 默认开启；未使用 -p（no promiscuous mode）参数。",
    ]
)
make("02_Wireshark接口与混杂模式", "Wireshark 接口与混杂模式", interfaces, 80)

overview = "\n\n".join(
    [
        "=== capinfos ===",
        run([CAPINFOS, PCAP]),
        "=== Protocol Hierarchy Statistics ===",
        run([TSHARK, "-r", PCAP, "-q", "-z", "io,phs"]),
    ]
)
make("03_抓包概览与协议统计", "抓包概览与协议统计", overview, 105)

packet_list = run(
    [
        TSHARK,
        "-r",
        PCAP,
        "-Y",
        "arp or icmp or dns or (tcp and ip) or udp",
        "-T",
        "fields",
        "-E",
        "header=y",
        "-E",
        "separator= | ",
        "-e",
        "frame.number",
        "-e",
        "frame.time_relative",
        "-e",
        "_ws.col.Protocol",
        "-e",
        "_ws.col.Source",
        "-e",
        "_ws.col.Destination",
        "-e",
        "_ws.col.Info",
    ]
)
filters = "\n".join(
    [
        "常用显示过滤器：arp / icmp / tcp / udp / dns",
        "本机 IPv4：ip.addr == 192.168.138.120",
        "网关/DNS：ip.addr == 192.168.138.246",
        "",
        packet_list,
    ]
)
make("04_过滤器与关键数据流", "过滤器与关键数据流", filters, 120)

make("05_ARP报文细节", "ARP 报文细节", run([TSHARK, "-r", PCAP, "-Y", "frame.number==21 or frame.number==22 or frame.number==39 or frame.number==40", "-V"]), 110)
make("06_IP_ICMP报文细节", "IP / ICMP 报文细节", run([TSHARK, "-r", PCAP, "-Y", "frame.number==13 or frame.number==14", "-V"]), 130)
make("07_TCP报文细节", "TCP 报文细节", run([TSHARK, "-r", PCAP, "-Y", "frame.number==24", "-V"]), 120)
make("08_UDP_DNS报文细节", "UDP / DNS 报文细节", run([TSHARK, "-r", PCAP, "-Y", "frame.number==80 or frame.number==82", "-V"]), 130)

conversations = "\n\n".join(
    [
        run([TSHARK, "-r", PCAP, "-q", "-z", "conv,ip"]),
        run([TSHARK, "-r", PCAP, "-q", "-z", "conv,tcp"]),
        run([TSHARK, "-r", PCAP, "-q", "-z", "conv,udp"]),
    ]
)
make("09_会话统计", "Wireshark 会话统计", conversations, 120)

notes = """实验2已完成的证据文件：
1. exp2_mix.pcapng：原始抓包文件，接口 WLAN，122 个包，0 丢包。
2. filter_arp.pcapng / filter_icmp.pcapng / filter_tcp_ipv4.pcapng / filter_udp_dns.pcapng：按协议过滤后的包。
3. 01-09 PNG：可直接放入实验报告的截图。

报告可写的关键包号：
ARP：21/22/39/40
ICMP：13/14
IPv4 + TCP：24
UDP/DNS：80/82
"""
save_text("实验2说明", notes)

