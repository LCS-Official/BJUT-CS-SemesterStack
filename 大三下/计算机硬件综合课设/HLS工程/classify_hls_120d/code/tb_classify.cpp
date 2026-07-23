#include <stdint.h>
#include <stdio.h>
#include "hls_stream.h"
#include "ap_axi_sdata.h"
#include "practical_svm_weights_eyefeature_binary.h"

typedef ap_axiu<32, 0, 0, 0> axis_t;

void classify(
    hls::stream<axis_t> &in_stream,
    hls::stream<axis_t> &out_stream,
    int32_t threshold_q
);

static axis_t make_word(int32_t data, bool last=false) {
    axis_t w;
    w.data = (uint32_t)data;
    w.keep = -1;
    w.strb = -1;
    w.last = last ? 1 : 0;
    return w;
}

static int sw_classify(const int32_t x[SVM_INPUT_DIM], int64_t *score_out) {
    int64_t acc = SVM_B_PRACTICAL;
    for (int i = 0; i < SVM_INPUT_DIM; ++i) {
        acc += (int64_t)SVM_W[i] * (int64_t)x[i];
    }
    if (score_out) *score_out = acc;
    return (acc > 0) ? 1 : 0;
}

static int32_t sw_score_q(int64_t acc) {
    const int shift = 12;
    const int64_t scale = 1LL << shift;
    int64_t q = 0;
    if (acc >= 0) {
        q = acc / scale;
    } else {
        q = -(((-acc) + scale - 1) / scale);
    }
    if (q > 2147483647LL) return 2147483647;
    if (q < -2147483648LL) return (int32_t)0x80000000u;
    return (int32_t)q;
}

static int run_case(const char *name, const int32_t x[SVM_INPUT_DIM]) {
    hls::stream<axis_t> in_stream;
    hls::stream<axis_t> out_stream;
    for (int i = 0; i < SVM_INPUT_DIM; ++i) {
        in_stream.write(make_word(x[i], i == SVM_INPUT_DIM - 1));
    }

    classify(in_stream, out_stream, 0);
    if (out_stream.empty()) {
        printf("测试失败！ %s 产生无输出\n", name);
        return 1;
    }
    axis_t out_pred = out_stream.read();
    if (out_stream.empty()) {
        printf("测试失败！%s 产生没有分数输出\n", name);
        return 1;
    }
    axis_t out_score = out_stream.read();
    int got = (int)out_pred.data;
    int32_t got_score_q = (int32_t)out_score.data;
    int64_t score = 0;
    int exp = sw_classify(x, &score);
    int32_t exp_score_q = sw_score_q(score);
    printf("[CASE] %s exp=%d got=%d score=%lld score_q exp=%d got=%d\n",
           name, exp, got, (long long)score, (int)exp_score_q, (int)got_score_q);
    if (got != exp) {
        printf("测试失败！%s 不匹配\n", name);
        return 1;
    }
    if (got_score_q != exp_score_q) {
        printf("测试失败！ %s score_q 不匹配\n", name);
        return 1;
    }
    if (!out_score.last) {
        printf("测试失败！%s 分数输出必须断言TLAST\n", name);
        return 1;
    }
    return 0;
}

int main() {
    int fails = 0;

    int32_t zero[SVM_INPUT_DIM];
    int32_t ramp[SVM_INPUT_DIM];
    int32_t pulse[SVM_INPUT_DIM];
    for (int i = 0; i < SVM_INPUT_DIM; ++i) {
        zero[i] = 0;
        ramp[i] = (i % 15) * 64;
        pulse[i] = (i / 15 == 0 || i / 15 == 1) ? 2400 : 0;
    }

    fails += run_case("zero", zero);
    fails += run_case("ramp", ramp);
    fails += run_case("pulse", pulse);

    if (fails == 0) {
        printf("测试通过！classify 120D C 测试通过. SVM_INPUT_DIM=%d\n", SVM_INPUT_DIM);
    }
    return fails;
}
