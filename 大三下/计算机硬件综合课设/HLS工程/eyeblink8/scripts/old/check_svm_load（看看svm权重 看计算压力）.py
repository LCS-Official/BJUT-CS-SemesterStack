import joblib

model = joblib.load(r"svm_runs\three_class_mixed_v2_rbf_customw\svm_model.joblib")
svc = model.named_steps["svc"]
scaler = model.named_steps["scaler"]

print("classes:", svc.classes_)
print("n_support:", svc.n_support_)
print("total support vectors:", svc.support_vectors_.shape)
print("dual_coef shape:", svc.dual_coef_.shape)
print("intercept shape:", svc.intercept_.shape)
print("gamma:", svc._gamma)

print("scaler mean shape:", scaler.mean_.shape)
print("scaler scale shape:", scaler.scale_.shape)