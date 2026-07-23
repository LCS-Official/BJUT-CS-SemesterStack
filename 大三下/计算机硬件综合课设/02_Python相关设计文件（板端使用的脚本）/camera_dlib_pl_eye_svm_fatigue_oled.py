# PYNQ板端的完整疲劳测试启动器

import sys
import importlib.util
from pathlib import Path


DEFAULT_ARGS = [
    "--bit", "/home/xilinx/LC_SVM/final_screen.bit",
    "--enable-fatigue-alert",
    "--enable-oled",
    "--oled-ip", "SPI_SCREEN",
    "--oled-controller", "ssd1309",
    "--oled-refresh-sec", "1.0",
    "--enable-standby",
    "--standby-after-sec", "10",
    "--standby-probe-sec", "5",
    "--seconds", "0",
    "--stream-csv",
    "--out-csv", "/home/xilinx/LC_SVM/outputs/runtime/fatigue_oled_runtime.csv",
    "--no-hash",
    "--print-every", "5",
    "--dlib-decimate", "3",
    "--detect-interval", "1",
    "--reuse-max-age", "8",
    "--pl-interval", "1",
    "--svm-every", "1",
    "--svm-threshold-q", "0",
    "--post-closed-hold", "0",
    "--fatigue-score-threshold-q", "0",
    "--fatigue-window-sec", "10",
    "--fatigue-on-ratio", "0.25",
    "--fatigue-off-ratio", "0.10",
    "--fatigue-min-samples", "25",
    "--fatigue-clear-open-sec", "4",
    "--alert-min-sec", "3",
    "--led-repeat-sec", "3.25",
    "--tts-cooldown-sec", "20",
]


def main():
    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir))
    sys.argv = [sys.argv[0]] + DEFAULT_ARGS + sys.argv[1:]

    try:
        from camera_dlib_pl_eye_svm_integration_oled import main as integration_main
    except ModuleNotFoundError:
        local_copy = script_dir / "camera_dlib_pl_eye_svm_integration_oled.remote.py"
        spec = importlib.util.spec_from_file_location("camera_dlib_pl_eye_svm_integration_oled", local_copy)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        integration_main = module.main

    integration_main()


if __name__ == "__main__":
    main()
