# 大语言模型空间建模能力的认知边界与逻辑一致性挖掘分析

本项目当前阶段聚焦老师提供的一个楼梯转角题目，先跑通完整流程：多模态采集、自动预标注、人工复核、统计分析。

## 当前题目

模型需要判断一台电动轮椅能否通过真实楼梯转角。

输入给模型的材料：

- `楼梯转角实地图.jpg`：发送给多模态模型的真实照片。
- 文字题面：提供全部尺寸数字和运动约束。

不发送给模型的材料：

- `题目示意图.png`：只供我们整理题面和参考答案使用，不能作为模型输入。

## 关键尺寸与约束

- 轮椅尺寸：前后长 `121cm`，左右宽 `68.5cm`。
- 左侧主平台竖向净长：约 `140cm`。
- 左下入口净宽：约 `110cm`。
- 右下出口净宽：约 `110cm`。
- 右侧竖向区域净宽：约 `70cm`。
- 右上井道宽：约 `70cm`，不可通过。
- 中右部斜向边界：约 `106cm`。
- 斜边两端附近各有约 `15cm` 短边。
- 运动约束：轮椅只能沿当前朝向直线前进或后退；需要转弯时必须停下调转方向，不能连续弧线转弯。

## 当前数据集

`data/prompt_matrix_seed.csv` 已调整为单一场景 `T1`：

- 12 条 Prompt。
- 全部使用 `楼梯转角实地图.jpg`。
- 覆盖三种严格区分的表述层级：
  - `L1`：自然语言和照片理解层，不给厘米级尺寸数字。
  - `L2`：完整参数层，给出全部尺寸。
  - `L3`：形式化建模层，表述为矩形刚体、配置空间或碰撞检测问题。
- 参考结论为 `pass`，但模型不会看到示意图中的红框。

## 运行流程

建议新一轮数据使用新的输出文件，避免和旧版八场景数据混用。

1. 确认模型配置。

```powershell
Copy-Item configs\models.example.json configs\models.json
$env:YUNWU_API_KEY="你的云雾 API Key"
```

本轮会发送图片输入，因此 `configs/models.json` 中的模型必须支持视觉/多模态输入。如果某个模型返回“不支持 image_url”之类的错误，需要在云雾控制台换成同系列的视觉模型，或先从本轮配置中移除该模型。

2. 采集多模态回答。

```powershell
python src\collect_responses.py --prompts data\prompt_matrix_seed.csv --models configs\models.json --repeat 2 --out data\raw\responses_teacher.csv
```

3. 生成待标注表。

```powershell
python src\prepare_annotation.py --input data\raw\responses_teacher.csv --out data\processed\annotated_responses_teacher.csv
```

4. 自动预标注。

```powershell
Copy-Item configs\annotator.example.json configs\annotator.json
python src\auto_annotate.py --input data\processed\annotated_responses_teacher.csv --out data\processed\annotated_responses_teacher_auto.csv --config configs\annotator.json
```

5. 人工复核。

优先核对：

- `review_required=1`。
- `failure_mode` 不是 `no_error`。
- `is_correct=0`。
- 每个模型随机抽样 10% 到 20%。

6. 统计分析。

```powershell
python src\analyze_results.py --input data\processed\annotated_responses_teacher_auto.csv --out outputs_teacher
```

## 多模态输入实现

`src/collect_responses.py` 支持 `image_path` 字段。CSV 中的 `image_path=楼梯转角实地图.jpg` 会被编码为 base64 data URL，并按 OpenAI-compatible 多模态格式发送。

脚本有保护逻辑：如果 `image_path` 指向 `题目示意图.png`，会直接报错，避免误把带答案提示的示意图发送给模型。

## 主要交付物

- 多模态 AI 行为数据集：`data/raw/responses_teacher.csv`。
- 自动/人工复核后的标注表：`data/processed/annotated_responses_teacher_auto.csv`。
- 分析输出：`outputs_teacher`。
- 课程报告：重点讨论单一真实场景下模型对尺寸、照片、井道不可通行约束和直线运动约束的理解边界。
