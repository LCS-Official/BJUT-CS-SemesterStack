#pragma once
#include <stdint.h>

// Robust upright 30D binary EyeFeature SVM. score_q > 0 => closed.
// Trained from board recordings with local dlib_decimate=1 and HLS-matched robust EyeFeature.
#define SVM_INPUT_DIM 30
#define SVM_INPUT_SCALE 4096
#define SVM_WEIGHT_SCALE 1048576
#define SVM_THRESHOLD_FLOAT -0.0196

static const int32_t SVM_W[SVM_INPUT_DIM] = {
    -467947, -418102, -414578, -413440, -400131, -401654, -338217, -324505, -295306, -240174, -218592, -216819, -230742, -199817, -163232, 952792, 850406, 780633, 738290, 695929, 687350, 725480, 721809, 638748, 605186, 622306, 674947, 704846, 741684, 828364
};
static const int64_t SVM_B_ZERO_THRESHOLD = -17450204117;
static const int64_t SVM_THRESHOLD_Q = -84181359;
static const int64_t SVM_B_PRACTICAL = -17366022758;
