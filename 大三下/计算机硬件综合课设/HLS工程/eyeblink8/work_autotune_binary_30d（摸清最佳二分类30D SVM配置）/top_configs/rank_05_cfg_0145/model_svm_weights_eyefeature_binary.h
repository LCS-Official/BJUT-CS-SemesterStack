#pragma once
#include <stdint.h>

// Binary EyeFeature SVM. Tuned deployment bias is folded: score_q > 0 => closed.
#define SVM_INPUT_DIM 30
#define SVM_INPUT_SCALE 4096
#define SVM_WEIGHT_SCALE 1048576
#define SVM_BEST_THRESHOLD_FLOAT 0.718138552

static const int32_t SVM_W[SVM_INPUT_DIM] = {-1097963, -42924, -134163, -100134, -146868, -67890, -74401, -193830, -142043, 89079, -159177, -144326, -188386, -135920, -882688, -99551, 37471, -19322, 94408, -28205, -126771, 183969, 41332, -155156, 26880, 24197, 88171, 413472, 77957, -278066};
static const int64_t SVM_B_ZERO_THRESHOLD = 8279717000;
static const int64_t SVM_THRESHOLD_Q = 3084381593;
static const int64_t SVM_B_TUNED = 5195335407;
