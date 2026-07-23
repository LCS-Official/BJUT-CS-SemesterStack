import time
import torch
import torch.nn as nn
import torch.optim as optim
import xgboost as xgb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus'] = False 

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

print("拓展实验：算力拐点与特征鲁棒性")

# ==========================================
# 0. 基础数据准备
# ==========================================
columns = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'label']
df = pd.read_csv('./iris_data.txt', header=None, names=columns)
df = df[df['label'].isin(['Iris-setosa', 'Iris-versicolor'])]
df['label'] = df['label'].map({'Iris-setosa': 0, 'Iris-versicolor': 1})

X_base = df.iloc[:, :-1].values
y_base = df.iloc[:, -1].values
device = torch.device("xpu" if torch.xpu.is_available() else "cpu")

# MLP 动态模型定义
class MLP(nn.Module):
    def __init__(self, input_dim):
        super(MLP, self).__init__()
        self.fc1 = nn.Linear(input_dim, 16)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()
    def forward(self, x):
        return self.sigmoid(self.fc2(self.relu(self.fc1(x))))

# ==========================================
# 拓展实验一：数据规模放大与算力拐点测试
# ==========================================
print("\n>>> 开始进行 [拓展实验一：算力拐点测试]...")
scales = [1, 10, 100, 500, 1000] # 数据复制倍数 (80 -> 80,000 条训练数据)
mlp_times = []
xgb_times = []
sample_sizes = []

for scale in scales:
    # 按照倍数复制数据
    X_scaled_up = np.tile(X_base, (scale, 1))
    y_scaled_up = np.tile(y_base, scale)
    
    X_tr, _, y_tr, _ = train_test_split(X_scaled_up, y_scaled_up, test_size=0.2, random_state=42)
    scaler = StandardScaler()
    X_tr_std = scaler.fit_transform(X_tr)
    sample_sizes.append(len(X_tr_std))
    
    # --- 测试 XGBoost ---
    model_xgb = xgb.XGBClassifier(n_estimators=50, max_depth=3, eval_metric='logloss', random_state=42)
    t0 = time.perf_counter()
    model_xgb.fit(X_tr_std, y_tr)
    xgb_times.append((time.perf_counter() - t0) * 1000)
    
    # --- 测试 PyTorch MLP ---
    model_mlp = MLP(input_dim=4).to(device)
    optimizer = optim.Adam(model_mlp.parameters(), lr=0.05)
    criterion = nn.BCELoss()
    X_tensor = torch.FloatTensor(X_tr_std).to(device)
    y_tensor = torch.FloatTensor(y_tr).view(-1, 1).to(device)
    
    t0 = time.perf_counter()
    for _ in range(150):
        optimizer.zero_grad()
        loss = criterion(model_mlp(X_tensor), y_tensor)
        loss.backward()
        optimizer.step()
    if device.type == 'xpu':
        torch.xpu.synchronize()
    mlp_times.append((time.perf_counter() - t0) * 1000)

# 画图：算力拐点
plt.figure(figsize=(8, 5))
plt.plot(sample_sizes, mlp_times, marker='o', label='PyTorch MLP (XPU)', color='b', linewidth=2)
plt.plot(sample_sizes, xgb_times, marker='s', label='XGBoost (CPU)', color='g', linewidth=2)
plt.xscale('log')
plt.yscale('log')
plt.title('训练时间-数据集大小的算力拐点研究')
plt.xlabel('训练样本数（log值）')
plt.ylabel('训练时间（log值，ms）')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig('hardware_crossover.png', dpi=300)
plt.close()
print("    图表已保存: hardware_crossover.png")

# ==========================================
# 拓展实验二：注入“垃圾特征”的维度灾难测试
# ==========================================
print("\n>>> 开始进行 [拓展实验二：无关特征鲁棒性测试]...")
noise_feature_counts = [0, 10, 50, 100, 200]
mlp_accs = []
xgb_accs = []

X_tr_base, X_te_base, y_tr, y_te = train_test_split(X_base, y_base, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_tr_base = scaler.fit_transform(X_tr_base)
X_te_base = scaler.transform(X_te_base)

for n_noise in noise_feature_counts:
    # 生成纯随机的高斯噪声特征
    np.random.seed(42)
    noise_train = np.random.randn(X_tr_base.shape[0], n_noise)
    noise_test = np.random.randn(X_te_base.shape[0], n_noise)
    
    # 拼接到原始特征后面
    X_tr_noisy = np.hstack((X_tr_base, noise_train)) if n_noise > 0 else X_tr_base
    X_te_noisy = np.hstack((X_te_base, noise_test)) if n_noise > 0 else X_te_base
    
    # --- 测试 XGBoost ---
    model_xgb = xgb.XGBClassifier(n_estimators=50, max_depth=3, eval_metric='logloss', random_state=42)
    model_xgb.fit(X_tr_noisy, y_tr)
    xgb_accs.append(accuracy_score(y_te, model_xgb.predict(X_te_noisy)))
    
    # --- 测试 PyTorch MLP ---
    model_mlp = MLP(input_dim=4 + n_noise).to(device)
    optimizer = optim.Adam(model_mlp.parameters(), lr=0.05)
    criterion = nn.BCELoss()
    X_tr_tensor = torch.FloatTensor(X_tr_noisy).to(device)
    y_tr_tensor = torch.FloatTensor(y_tr).view(-1, 1).to(device)
    X_te_tensor = torch.FloatTensor(X_te_noisy).to(device)
    
    for _ in range(150):
        optimizer.zero_grad()
        loss = criterion(model_mlp(X_tr_tensor), y_tr_tensor)
        loss.backward()
        optimizer.step()
        
    model_mlp.eval()
    with torch.no_grad():
        preds = (model_mlp(X_te_tensor).cpu().numpy() >= 0.5).astype(int).flatten()
        mlp_accs.append(accuracy_score(y_te, preds))

# 画图：无关特征鲁棒性
plt.figure(figsize=(8, 5))
plt.plot(noise_feature_counts, mlp_accs, marker='o', label='PyTorch MLP', color='b', linewidth=2)
plt.plot(noise_feature_counts, xgb_accs, marker='s', label='XGBoost', color='g', linewidth=2)
plt.title('无关特征鲁棒性')
plt.xlabel('添加的无关噪声特征')
plt.ylabel('测试集准确率')
plt.ylim(0.4, 1.05)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig('noise_feature_robustness.png', dpi=300)
plt.close()
print("    图表已保存: noise_feature_robustness.png")
print("\n>>> 所有拓展实验运行完毕！")