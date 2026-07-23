#pragma once
#include <stdint.h>

// Binary EyeFeature SVM. Tuned deployment bias is folded: score_q > 0 => closed.
#define SVM_INPUT_DIM 30
#define SVM_INPUT_SCALE 4096
#define SVM_WEIGHT_SCALE 1048576
#define SVM_BEST_THRESHOLD_FLOAT 0.560358485

static const int32_t SVM_W[SVM_INPUT_DIM] = {-1105110, -64826, -154909, -116765, -149726, -91432, -51955, -168498, -128372, 52748, -179535, -130841, -161664, -134255, -907263, -128075, 56549, -43552, 107631, -3926, -167795, 171415, 50037, -189377, 71218, 13491, 45381, 419291, 72907, -305614};
static const int64_t SVM_B_ZERO_THRESHOLD = 7865132261;
static const int64_t SVM_THRESHOLD_Q = 2406721369;
static const int64_t SVM_B_TUNED = 5458410892;
