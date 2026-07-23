#pragma once
#include <stdint.h>

// Binary EyeFeature SVM. score_q > 0 => closed, else non_closed.
#define SVM_INPUT_DIM 30
#define SVM_INPUT_SCALE 4096
#define SVM_WEIGHT_SCALE 1048576

static const int32_t SVM_W[SVM_INPUT_DIM] = {1811625, -77142, -211342, 520369, -109793, -315897, -121073, 18629, 345471, -380552, 1056736, -203550, -172542, 682584, 765296, -4185567, 295364, 99448, -1140919, -25409, -10578, -571107, 103090, -150419, -370330, -358288, -369415, -406687, -63588, -3474261};
static const int64_t SVM_B = 14066036968;
