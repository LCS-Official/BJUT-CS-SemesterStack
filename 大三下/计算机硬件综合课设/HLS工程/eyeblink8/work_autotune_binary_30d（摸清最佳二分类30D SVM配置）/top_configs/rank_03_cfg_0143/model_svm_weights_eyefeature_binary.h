#pragma once
#include <stdint.h>

// Binary EyeFeature SVM. Tuned deployment bias is folded: score_q > 0 => closed.
#define SVM_INPUT_DIM 30
#define SVM_INPUT_SCALE 4096
#define SVM_WEIGHT_SCALE 1048576
#define SVM_BEST_THRESHOLD_FLOAT 0.44835797

static const int32_t SVM_W[SVM_INPUT_DIM] = {-1116382, -68863, -176727, -116633, -149106, -121335, -22236, -163418, -118243, 26511, -190854, -126503, -130477, -138107, -922128, -121211, 54858, -36215, 102859, 13220, -171230, 132954, 77844, -203795, 91907, 28501, 20551, 396177, 57181, -270407};
static const int64_t SVM_B_ZERO_THRESHOLD = 7418237015;
static const int64_t SVM_THRESHOLD_Q = 1925682819;
static const int64_t SVM_B_TUNED = 5492554196;
