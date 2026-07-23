#pragma once
#include <stdint.h>

static const int SVM_NUM_CLASSES = 3;
static const int SVM_FEATURE_DIM = 15;
static const int SVM_FIXED_SCALE = 4096;

static const int32_t SVM_CLASS_IDS[3] = {0, 1, 2};

static const int32_t SVM_B[3] = {
    -9229,
    -30,
    17913
};

static const int32_t SVM_W[3][15] = {
    {-11304, 8440, 13065, 9915, 2159, 4395, -438, -4941, -3006, -325, 20962, 28247, 11933, -4104, -31770},
    {16650, -9472, -12364, -8400, -1683, -2694, 4938, 8235, 5522, 3742, -20835, -29768, -10847, 7011, 40857},
    {-13308, -3100, -2754, -959, -1960, -8693, -8912, -9128, -8218, -4588, -4241, -7294, -4254, -8079, -13260}
};
