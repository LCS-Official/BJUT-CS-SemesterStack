# Practical Binary 30D EyeFeature SVM Export

## Chosen config

- config_id: 193
- feature_names: col_run_max_fixed+col_run_topk_adapt
- dataset_rule_name: std_7_6_openonly
- C: 1.0
- class_weight: balanced
- threshold used for export: 0.0
- input_dim: 30

## Metrics with exported threshold

- train: acc=0.9226, macro_f1=0.8295, closed_precision=0.6324, closed_recall=0.7928, false_closed_rate=0.0604, missed_closed_rate=0.2072, cm=[[16430,1056],[475,1817]]
- val: acc=0.9352, macro_f1=0.8761, closed_precision=0.6537, closed_recall=1.0000, false_closed_rate=0.0738, missed_closed_rate=0.0000, cm=[[2460,196],[0,370]]
- test: acc=0.8766, macro_f1=0.7868, closed_precision=0.7891, closed_recall=0.5504, false_closed_rate=0.0384, missed_closed_rate=0.4496, cm=[[1354,54],[165,202]]

## HLS rule

```c
x_q[i] = round(feature[i] * SVM_INPUT_SCALE);
score_q = sum(SVM_W[i] * x_q[i]) + SVM_B_PRACTICAL;
pred_closed = (score_q > 0);
```

## Files

- practical_svm_weights_eyefeature_binary.h
- practical_linear_export_binary.json
- practical_model.joblib
- per_video_metrics.csv
- train_predictions.csv / val_predictions.csv / test_predictions.csv
