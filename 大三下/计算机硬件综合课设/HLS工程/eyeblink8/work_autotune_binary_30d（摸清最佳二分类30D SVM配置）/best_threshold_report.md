# Binary 30D EyeFeature AutoTune Best Result

## Best config

- config_id: 141
- feature_names: col_run_max_fixed+col_run_topk_adapt
- dataset_rule_name: strict_9_8_openstep3_blinkasnonclosed
- central_size: 9
- min_closed_in_central: 8
- open_step: 3
- eyeblink8_policy: open_blink_as_nonclosed
- C: 0.03
- class_weight: balanced
- best_threshold: 0.7181570173548436
- rank_score: 0.9971373904272921

## Key metrics

- val_tuned_accuracy: 0.998291
- val_tuned_macro_f1: 0.994743
- val_tuned_closed_precision: 0.981030
- val_tuned_closed_recall: 1.000000
- val_tuned_false_closed_rate: 0.001874
- val_tuned_missed_closed_rate: 0.000000
- test_tuned_accuracy: 0.853135
- test_tuned_macro_f1: 0.471292
- test_tuned_closed_precision: 0.800000
- test_tuned_closed_recall: 0.011142
- test_tuned_false_closed_rate: 0.000484
- test_tuned_missed_closed_rate: 0.988858
- test_zero_closed_recall: 0.415042
- test_zero_false_closed_rate: 0.076513

## Top 10 configs

 config_id                        feature_names                     dataset_rule_name    C          class_weight  best_threshold  rank_score  val_tuned_closed_recall  val_tuned_false_closed_rate  val_tuned_macro_f1  test_tuned_closed_recall  test_tuned_false_closed_rate  test_tuned_macro_f1
       141 col_run_max_fixed+col_run_topk_adapt strict_9_8_openstep3_blinkasnonclosed 0.03              balanced        0.718157    0.997137                      1.0                     0.001874            0.994743                  0.011142                      0.000484             0.471292
       142 col_run_max_fixed+col_run_topk_adapt strict_9_8_openstep3_blinkasnonclosed 0.03 non_closed:1,closed:2        0.363626    0.997137                      1.0                     0.001874            0.994743                  0.011142                      0.000484             0.471292
       143 col_run_max_fixed+col_run_topk_adapt strict_9_8_openstep3_blinkasnonclosed 0.03 non_closed:1,closed:3        0.448358    0.997137                      1.0                     0.001874            0.994743                  0.011142                      0.000484             0.471292
       144 col_run_max_fixed+col_run_topk_adapt strict_9_8_openstep3_blinkasnonclosed 0.03 non_closed:1,closed:5        0.560358    0.997137                      1.0                     0.001874            0.994743                  0.011142                      0.000484             0.471292
       145 col_run_max_fixed+col_run_topk_adapt strict_9_8_openstep3_blinkasnonclosed 0.10              balanced        0.718139    0.997137                      1.0                     0.001874            0.994743                  0.011142                      0.000484             0.471292
       146 col_run_max_fixed+col_run_topk_adapt strict_9_8_openstep3_blinkasnonclosed 0.10 non_closed:1,closed:2        0.362629    0.997137                      1.0                     0.001874            0.994743                  0.011142                      0.000484             0.471292
       147 col_run_max_fixed+col_run_topk_adapt strict_9_8_openstep3_blinkasnonclosed 0.10 non_closed:1,closed:3        0.447380    0.997137                      1.0                     0.001874            0.994743                  0.011142                      0.000484             0.471292
       148 col_run_max_fixed+col_run_topk_adapt strict_9_8_openstep3_blinkasnonclosed 0.10 non_closed:1,closed:5        0.559528    0.997137                      1.0                     0.001874            0.994743                  0.011142                      0.000484             0.471292
       149 col_run_max_fixed+col_run_topk_adapt strict_9_8_openstep3_blinkasnonclosed 0.30              balanced        0.717998    0.997137                      1.0                     0.001874            0.994743                  0.011142                      0.000484             0.471292
       150 col_run_max_fixed+col_run_topk_adapt strict_9_8_openstep3_blinkasnonclosed 0.30 non_closed:1,closed:2        0.362342    0.997137                      1.0                     0.001874            0.994743                  0.011142                      0.000484             0.471292