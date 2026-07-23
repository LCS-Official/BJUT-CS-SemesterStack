#include <stdint.h>
#include <stdio.h>
#include <vector>
#include "hls_stream.h"
#include "ap_axi_sdata.h"

typedef ap_axiu<32, 0, 0, 0> axis_word_t;

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
);

static axis_word_t make_word(uint32_t data, bool last=false) {
    axis_word_t w;
    w.data = data;
    w.keep = 0xF;
    w.strb = 0xF;
    w.last = last ? 1 : 0;
    return w;
}

static std::vector<int> run_case(const char *name, int bg, int line, bool draw_line) {
    const int W = 96;
    const int H = 64;
    uint8_t frame[H][W];
    for (int y = 0; y < H; ++y) {
        for (int x = 0; x < W; ++x) {
            frame[y][x] = (uint8_t)bg;
        }
    }
    if (draw_line) {
        for (int y = 22; y < 46; ++y) {
            for (int x = 22; x < 27; ++x) frame[y][x] = (uint8_t)line;
            for (int x = 68; x < 73; ++x) frame[y][x] = (uint8_t)line;
        }
    }

    hls::stream<axis_word_t> in_stream;
    hls::stream<axis_word_t> out_stream;
    for (int y = 0; y < H; ++y) {
        for (int x = 0; x < W; ++x) {
            bool last = (y == H - 1) && (x == W - 1);
            in_stream.write(make_word(frame[y][x], last));
        }
    }

    eye_feature(
        in_stream, out_stream,
        W, H,
        12, 12, 32, 44,
        58, 12, 32, 44,
        1,
        10, 60, 4096,
        0,
        123
    );

    std::vector<int> out;
    while (!out_stream.empty()) {
        axis_word_t w = out_stream.read();
        out.push_back((int)w.data);
    }
    printf("[CASE] %s words=%d", name, (int)out.size());
    for (int i = 0; i < (int)out.size(); ++i) {
        printf(" %d", out[i]);
    }
    printf("\n");
    return out;
}

int main() {
    int fails = 0;
    std::vector<int> open = run_case("open", 110, 35, true);
    std::vector<int> bright = run_case("open_brighter", 170, 95, true);
    std::vector<int> flat = run_case("flat_no_contrast", 180, 180, false);

    if (open.size() != 11 || bright.size() != 11 || flat.size() != 11) {
        printf("测试失败！预期每次运行 11个输出word\n");
        return 1;
    }
    if (open[8] != 1 || bright[8] != 1 || flat[8] != 1) {
        printf("测试失败！有效flag不匹配\n");
        fails++;
    }
    for (int i = 0; i < 8; ++i) {
        if (open[i] != bright[i]) {
            printf("测试失败！亮度不变性不匹配特征[%d]: %d vs %d\n", i, open[i], bright[i]);
            fails++;
        }
    }
    for (int i = 0; i < 8; ++i) {
        if (flat[i] != 0) {
            printf("测试失败！平铺无辨识性特征[%d] 预期0个，得到 %d\n", i, flat[i]);
            fails++;
        }
    }
    if (open[9] != 123 || bright[9] != 123 || flat[9] != 123) {
        printf("测试失败！ROI版本有问题\n");
        fails++;
    }
    if (fails == 0) {
        printf("测试通过！\n");
    }
    return fails;
}
