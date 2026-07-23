#pragma once
#include <stdint.h>

// Binary EyeFeature SVM. Tuned deployment bias is folded: score_q > 0 => closed.
#define SVM_INPUT_DIM 30
#define SVM_INPUT_SCALE 4096
#define SVM_WEIGHT_SCALE 1048576
#define SVM_BEST_THRESHOLD_FLOAT 0.363625976

static const int32_t SVM_W[SVM_INPUT_DIM] = {-1126970, -67269, -197732, -108665, -148857, -141601, -4649, -157042, -113829, 17242, -201825, -123034, -114093, -136724, -941879, -133205, 64656, -28229, 90486, 37574, -178278, 113693, 104732, -217075, 87643, 41616, 11167, 374108, 50754, -236565};
static const int64_t SVM_B_ZERO_THRESHOLD = 7077865180;
static const int64_t SVM_THRESHOLD_Q = 1561761674;
static const int64_t SVM_B_TUNED = 5516103506;
