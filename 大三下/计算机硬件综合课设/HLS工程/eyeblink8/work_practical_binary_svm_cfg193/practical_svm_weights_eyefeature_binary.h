#pragma once
#include <stdint.h>

// Practical binary EyeFeature SVM. score_q > 0 => closed.
// Inputs must be quantized as x_q[i] = round(feature[i] * SVM_INPUT_SCALE).
#define SVM_INPUT_DIM 30
#define SVM_INPUT_SCALE 4096
#define SVM_WEIGHT_SCALE 1048576
#define SVM_THRESHOLD_FLOAT 0

static const int32_t SVM_W[SVM_INPUT_DIM] = {
    -1267299,
    167736,
    11588,
    -286989,
    121975,
    -25274,
    -268623,
    -48918,
    -65105,
    -102229,
    53426,
    -253661,
    -257648,
    -10788,
    -1260383,
    12915,
    136586,
    -310668,
    -105447,
    129259,
    -345172,
    10238,
    267620,
    -246206,
    -276401,
    90792,
    -256337,
    68930,
    384663,
    30094
};
static const int64_t SVM_B_ZERO_THRESHOLD = 9956057115;
static const int64_t SVM_THRESHOLD_Q = 0;
static const int64_t SVM_B_PRACTICAL = 9956057115;

static inline int classify_eye_closed_binary(const int32_t x_q[SVM_INPUT_DIM]) {
    int64_t acc = SVM_B_PRACTICAL;
    for (int i = 0; i < SVM_INPUT_DIM; ++i) {
        acc += (int64_t)SVM_W[i] * (int64_t)x_q[i];
    }
    return acc > 0 ? 1 : 0; // 1=closed, 0=non_closed
}
