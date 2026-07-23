#pragma once
#include <stdint.h>

// Binary EyeFeature SVM. Tuned deployment bias is folded: score_q > 0 => closed.
#define SVM_INPUT_DIM 30
#define SVM_INPUT_SCALE 4096
#define SVM_WEIGHT_SCALE 1048576
#define SVM_BEST_THRESHOLD_FLOAT 0.718157017

static const int32_t SVM_W[SVM_INPUT_DIM] = {-1087794, -52792, -133367, -100260, -145587, -69937, -74896, -191624, -140757, 84050, -156893, -144579, -187212, -142902, -875285, -105091, 41755, -17608, 92193, -28370, -123086, 180655, 40864, -153046, 27383, 23850, 90480, 408617, 80878, -279902};
static const int64_t SVM_B_ZERO_THRESHOLD = 8278517047;
static const int64_t SVM_THRESHOLD_Q = 3084460903;
static const int64_t SVM_B_TUNED = 5194056144;
