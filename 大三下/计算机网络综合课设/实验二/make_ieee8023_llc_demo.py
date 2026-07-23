from pathlib import Path
import struct
import time


out = Path("实验2截图")
out.mkdir(exist_ok=True)
pcap = out / "ieee8023_llc_demo.pcap"

dst = bytes.fromhex("ff ff ff ff ff ff")
src = bytes.fromhex("02 00 00 00 00 01")
llc = bytes([0x12, 0x12, 0x03])
data = b"IEEE 802.3 LLC demo frame"
payload = (llc + data).ljust(46, b"\x00")
frame = dst + src + struct.pack("!H", len(payload)) + payload

ts = int(time.time())
with pcap.open("wb") as f:
    f.write(struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
    for i in range(3):
        f.write(struct.pack("<IIII", ts + i, 0, len(frame), len(frame)))
        f.write(frame)

print(pcap)
