import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score
import xgboost as xgb
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus'] = False 

print("=== 六大模型极限压力测试 ===")

columns = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'label']
df = pd.read_csv('./iris_data.txt', header=None, names=columns)
df = df[df['label'].isin(['Iris-setosa', 'Iris-versicolor'])]
df['label'] = df['label'].map({'Iris-setosa': 0, 'Iris-versicolor': 1})

X_base = df.iloc[:, :-1].values
y_base = df.iloc[:, -1].values
device = torch.device("xpu" if torch.xpu.is_available() else "cpu")

def get_sklearn_models():
    return {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Linear SVM": SVC(kernel='linear', random_state=42),
        "Decision Tree": DecisionTreeClassifier(max_depth=3, random_state=42),
        "Gaussian NB": GaussianNB(),
        "XGBoost": xgb.XGBClassifier(n_estimators=50, max_depth=3, eval_metric='logloss', random_state=42)
    }

# ==========================================
# 实验一：六大模型算力拐点测试 (耗时对比)
# ==========================================
print("\n>>> 开始 [算力拐点测试]...")
scales = [1, 10, 100, 500, 1000]
results_time = {name: [] for name in list(get_sklearn_models().keys()) + ["PyTorch MLP"]}
sample_sizes = []

for scale in scales:
    X_scaled_up = np.tile(X_base, (scale, 1))
    y_scaled_up = np.tile(y_base, scale)
    X_tr, _, y_tr, _ = train_test_split(X_scaled_up, y_scaled_up, test_size=0.2, random_state=42)
    X_tr_std = StandardScaler().fit_transform(X_tr)
    sample_sizes.append(len(X_tr_std))
    
    # 测试 Sklearn & XGBoost
    models = get_sklearn_models()
    for name, model in models.items():
        t0 = time.perf_counter()
        model.fit(X_tr_std, y_tr)
        results_time[name].append((time.perf_counter() - t0) * 1000)
    
    # 测试 PyTorch MLP
    model_mlp = nn.Sequential(nn.Linear(4, 16), nn.ReLU(), nn.Linear(16, 1), nn.Sigmoid()).to(device)
    optimizer = optim.Adam(model_mlp.parameters(), lr=0.05)
    criterion = nn.BCELoss()
    X_t = torch.FloatTensor(X_tr_std).to(device)
    y_t = torch.FloatTensor(y_tr).view(-1, 1).to(device)
    
    t0 = time.perf_counter()
    for _ in range(150):
        optimizer.zero_grad()
        loss = criterion(model_mlp(X_t), y_t)
        loss.backward()
        optimizer.step()
    if device.type == 'xpu': torch.xpu.synchronize()
    results_time["PyTorch MLP"].append((time.perf_counter() - t0) * 1000)

plt.figure(figsize=(10, 6))
markers = ['o', 's', '^', 'D', 'v', 'p']
for (name, times), marker in zip(results_time.items(), markers):
    # PyTorch 和 XGBoost 线条加粗突出
    lw = 3 if name in ["PyTorch MLP", "XGBoost"] else 1.5
    alpha = 1.0 if name in ["PyTorch MLP", "XGBoost"] else 0.6
    plt.plot(sample_sizes, times, marker=marker, label=name, linewidth=lw, alpha=alpha)

plt.xscale('log')
plt.yscale('log')
plt.title('训练时间-数据集大小的算力拐点研究')
plt.xlabel('训练样本数（log值）')
plt.ylabel('训练时间（log值，ms）')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig('all_hardware_crossover.png', dpi=300)

# ==========================================
# 实验二：六大模型维度灾难测试 (抗噪能力)
# ==========================================
print(">>> 开始 [维度灾难测试]...")
noise_counts = [0, 10, 50, 100, 200, 500] # 增加到500个垃圾特征，彻底施压
results_acc = {name: [] for name in list(get_sklearn_models().keys()) + ["PyTorch MLP"]}

X_tr_base, X_te_base, y_tr, y_te = train_test_split(X_base, y_base, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_tr_base, X_te_base = scaler.fit_transform(X_tr_base), scaler.transform(X_te_base)

for n_noise in noise_counts:
    np.random.seed(42)
    X_tr_noisy = np.hstack((X_tr_base, np.random.randn(X_tr_base.shape[0], n_noise))) if n_noise > 0 else X_tr_base
    X_te_noisy = np.hstack((X_te_base, np.random.randn(X_te_base.shape[0], n_noise))) if n_noise > 0 else X_te_base
    
    models = get_sklearn_models()
    for name, model in models.items():
        model.fit(X_tr_noisy, y_tr)
        results_acc[name].append(accuracy_score(y_te, model.predict(X_te_noisy)))
    
    model_mlp = nn.Sequential(nn.Linear(4 + n_noise, 16), nn.ReLU(), nn.Linear(16, 1), nn.Sigmoid()).to(device)
    optimizer = optim.Adam(model_mlp.parameters(), lr=0.05)
    criterion = nn.BCELoss()
    X_tr_t, y_tr_t = torch.FloatTensor(X_tr_noisy).to(device), torch.FloatTensor(y_tr).view(-1, 1).to(device)
    X_te_t = torch.FloatTensor(X_te_noisy).to(device)
    
    for _ in range(150):
        optimizer.zero_grad()
        loss = criterion(model_mlp(X_tr_t), y_tr_t)
        loss.backward()
        optimizer.step()
    
    with torch.no_grad():
        preds = (model_mlp(X_te_t).cpu().numpy() >= 0.5).astype(int).flatten()
        results_acc["PyTorch MLP"].append(accuracy_score(y_te, preds))

plt.figure(figsize=(10, 6))
for (name, accs), marker in zip(results_acc.items(), markers):
    lw = 3 if name in ["PyTorch MLP", "XGBoost", "Decision Tree"] else 1.5
    plt.plot(noise_counts, accs, marker=marker, label=name, linewidth=lw)

plt.title('额外噪声鲁棒性')
plt.xlabel('额外噪声添加量')
plt.ylabel('测试集准确率')
plt.ylim(0.3, 1.05)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig('all_noise_robustness.png', dpi=300)
print(">>> 所有六大模型极限测试运行完毕！图片已保存。")