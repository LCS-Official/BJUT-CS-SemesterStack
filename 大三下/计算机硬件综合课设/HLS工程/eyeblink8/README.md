# eyeblink8

本项目的人脸关键点实验依赖以下外部预训练模型。为避免把大型第三方权重纳入课程资料仓库，模型文件不随仓库发布；使用时请下载到本目录下的 `models/` 文件夹，并保持表中的文件名。

## 外部模型

| 文件名 | 用途 | 上游来源与下载 |
| --- | --- | --- |
| `shape_predictor_68_face_landmarks.dat` | dlib 68 点人脸关键点模型，供特征提取脚本和板端脚本使用 | [dlib 项目](https://github.com/davisking/dlib) · [官方示例说明](https://github.com/davisking/dlib/blob/master/python_examples/face_landmark_detection.py) · [模型下载（`.bz2`）](https://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2) |
| `face_landmark_model.dat` | OpenCV Facemark Kazemi 模型 | [OpenCV contrib 下载配置](https://github.com/opencv/opencv_contrib/blob/4.x/modules/face/CMakeLists.txt) · [固定版本下载](https://raw.githubusercontent.com/opencv/opencv_3rdparty/8afa57abc8229d611c4937165d20e2a2d9fc5a12/face_landmark_model.dat) |
| `lbfmodel.yaml` | OpenCV Facemark LBF 模型 | [原始 GSoC 2017 项目](https://github.com/kurnianggoro/GSOC2017) · [模型文件](https://github.com/kurnianggoro/GSOC2017/blob/master/data/lbfmodel.yaml) · [直接下载](https://raw.githubusercontent.com/kurnianggoro/GSOC2017/master/data/lbfmodel.yaml) |

下载 dlib 模型后需先解压：

```bash
bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
```

> dlib 上游说明该 68 点模型基于 iBUG 300-W 数据集训练，相关数据集许可不允许商业使用；本项目仅作课程学习与实验复现。
