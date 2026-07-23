#pragma once
#include <stdint.h>

static const int SVM_NUM_CLASSES = 3;
static const int SVM_FEATURE_DIM = 15;
static const int SVM_FIXED_SCALE = 4096;

static const int32_t SVM_CLASS_IDS[3] = {0, 1, 2};

static const int32_t SVM_B[3] = {
    -9228,
    -30,
    17874
};

static const int32_t SVM_W[3][15] = {
    {-11298, 8434, 13061, 9914, 2163, 4392, -440, -4941, -3005, -318, 20956, 28234, 11928, -4104, -31752},
    {16645, -9467, -12362, -8399, -1685, -2692, 4938, 8235, 5522, 3737, -20831, -29759, -10844, 7012, 40843},
    {-13273, -3093, -2734, -960, -1956, -8655, -8913, -9126, -8196, -4583, -4232, -7260, -4245, -8065, -13238}
};
