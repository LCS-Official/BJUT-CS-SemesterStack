#pragma once
#include <stdint.h>

// Binary EyeFeature SVM. score_q > 0 => closed, else non_closed.
#define SVM_INPUT_DIM 30
#define SVM_INPUT_SCALE 4096
#define SVM_WEIGHT_SCALE 1048576

static const int32_t SVM_W[SVM_INPUT_DIM] = {80847, 8161, -31698, -50445, -40019, -64695, -79819, -85896, -123118, -105105, -108477, -114806, -113377, -63137, -27952, 546171, 429101, 360170, 339167, 329210, 297284, 264296, 240603, 263760, 288659, 303788, 324513, 367774, 442522, 526584};
static const int64_t SVM_B = -10733145092;
