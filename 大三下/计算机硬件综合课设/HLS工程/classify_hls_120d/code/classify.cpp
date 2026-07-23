#include <stdint.h>
#include "hls_stream.h"
#include "ap_axi_sdata.h"
#include "practical_svm_weights_eyefeature_binary.h"

// avg_diff8 120D binary SVM

typedef ap_axiu<32, 0, 0, 0> axis_t;
typedef int32_t data_t;
typedef int64_t acc_t;

#ifndef SVM_SCORE_SHIFT
#define SVM_SCORE_SHIFT 12
#endif

static data_t saturate_i32(acc_t v) {
#pragma HLS INLINE
    const acc_t I32_MAX_V = 2147483647LL;
    const acc_t I32_MIN_V = -2147483648LL;
    if (v > I32_MAX_V) return (data_t)I32_MAX_V;
    if (v < I32_MIN_V) return (data_t)I32_MIN_V;
    return (data_t)v;
}

static data_t score_to_q(acc_t acc) {
#pragma HLS INLINE
#if SVM_SCORE_SHIFT > 0
    const acc_t scale = (acc_t)1 << SVM_SCORE_SHIFT;
    acc_t q = 0;
    if (acc >= 0) {
        q = acc / scale;
    } else {
        q = -(((-acc) + scale - 1) / scale);
    }
    return saturate_i32(q);
#else
    return saturate_i32(acc);
#endif
}

static void write_axis_word(hls::stream<axis_t> &out_stream, data_t value, bool last) {
#pragma HLS INLINE
    axis_t out_pkt;
    out_pkt.data = (uint32_t)value;
    out_pkt.keep = -1;
    out_pkt.strb = -1;
    out_pkt.last = last ? 1 : 0;
    out_stream.write(out_pkt);
}

void classify(
    hls::stream<axis_t> &in_stream,
    hls::stream<axis_t> &out_stream,
    data_t threshold_q
) {
#pragma HLS INTERFACE axis port=in_stream
#pragma HLS INTERFACE axis port=out_stream
#pragma HLS INTERFACE s_axilite port=threshold_q bundle=CTRL
#pragma HLS INTERFACE s_axilite port=return bundle=CTRL

    data_t x[SVM_INPUT_DIM];
#pragma HLS ARRAY_PARTITION variable=x cyclic factor=8 dim=1

    READ_WINDOW:
    for (int i = 0; i < SVM_INPUT_DIM; ++i) {
#pragma HLS PIPELINE II=1
        axis_t in_pkt = in_stream.read();
        x[i] = (data_t)in_pkt.data;
    }

    acc_t acc = SVM_B_PRACTICAL;
    MAC_LOOP:
    for (int i = 0; i < SVM_INPUT_DIM; ++i) {
#pragma HLS PIPELINE II=1
        acc += (acc_t)SVM_W[i] * (acc_t)x[i];
    }

    data_t score_q = score_to_q(acc);
    data_t pred = (score_q > threshold_q) ? 1 : 0;

    write_axis_word(out_stream, pred, false);
    write_axis_word(out_stream, score_q, true);
}
