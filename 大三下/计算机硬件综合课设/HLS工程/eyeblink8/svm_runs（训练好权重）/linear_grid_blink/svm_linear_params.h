#pragma once
#include <stdint.h>

static const int SVM_NUM_CLASSES = 3;
static const int SVM_FEATURE_DIM = 15;
static const int SVM_FIXED_SCALE = 4096;

static const int32_t SVM_CLASS_IDS[3] = {0, 1, 2};

static const int32_t SVM_B[3] = {
    -14063,
    -5646,
    19709
};

static const int32_t SVM_W[3][15] = {
    {-9347, 8780, 18768, 17394, 7374, 3078, -5389, -8328, -1011, -433, 24666, 32861, 14599, -1517, -27725},
    {22508, -6540, -15246, -17226, -6520, 3501, 16480, 21857, 10286, 526, -20887, -25757, -8570, 11214, 41068},
    {-13161, -2241, -3522, -168, -854, -6579, -11091, -13529, -9275, -93, -3778, -7104, -6029, -9696, -13343}
};
