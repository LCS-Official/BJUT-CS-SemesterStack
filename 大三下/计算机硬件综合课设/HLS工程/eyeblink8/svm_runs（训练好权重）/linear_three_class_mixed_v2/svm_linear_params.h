#pragma once
#include <stdint.h>

static const int SVM_NUM_CLASSES = 3;
static const int SVM_FEATURE_DIM = 15;
static const int SVM_FIXED_SCALE = 4096;

static const int32_t SVM_CLASS_IDS[3] = {0, 1, 2};

static const int32_t SVM_B[3] = {
    -9229,
    -1046,
    18273
};

static const int32_t SVM_W[3][15] = {
    {-11304, 8440, 13065, 9915, 2159, 4395, -438, -4941, -3006, -325, 20962, 28247, 11933, -4104, -31770},
    {16345, -8413, -12112, -8419, -2355, -1941, 5776, 8924, 5553, 2227, -19681, -26594, -9908, 6959, 36638},
    {-13532, -3155, -2612, -1115, -2122, -8633, -9121, -9323, -8264, -4710, -4408, -7285, -4266, -8146, -13269}
};
