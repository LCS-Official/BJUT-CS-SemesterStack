import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus'] = False 

print("torch MLP Iris实验")

# 1. 数据读取与预处理
columns = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'label']
df = pd.read_csv('./iris_data.txt', header=None, names=columns)
df = df[df['label'].isin(['Iris-setosa', 'Iris-versicolor'])]
df['label'] = df['label'].map({'Iris-setosa': 0, 'Iris-versicolor': 1})

X = df.iloc[:, :-1].values
y = df.iloc[:, -1].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 2. 模型定义与设备分配
device = torch.device("xpu" if torch.xpu.is_available() else "cpu")
print(f"当前计算设备: {device}")

X_train_tensor = torch.FloatTensor(X_train_scaled).to(device)
y_train_tensor = torch.FloatTensor(y_train).view(-1, 1).to(device)
X_test_tensor = torch.FloatTensor(X_test_scaled).to(device)

class MLP(nn.Module):
    def __init__(self, input_dim):
        super(MLP, self).__init__()
        self.fc1 = nn.Linear(input_dim, 16)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        return self.sigmoid(self.fc2(self.relu(self.fc1(x))))

model = MLP(input_dim=4).to(device)
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.05)

# 3. 模型训练
epochs = 150
loss_history = []
start_time = time.perf_counter()

for epoch in range(epochs):
    optimizer.zero_grad()
    outputs = model(X_train_tensor)
    loss = criterion(outputs, y_train_tensor)
    loss.backward()
    optimizer.step()
    loss_history.append(loss.item())

if device.type == 'xpu':
    torch.xpu.synchronize()
train_time = (time.perf_counter() - start_time) * 1000

# 4. 模型评估
model.eval()
with torch.no_grad():
    preds = (model(X_test_tensor) >= 0.5).float().cpu().numpy()
accuracy = accuracy_score(y_test, preds)

print(f"训练耗时: {train_time:.2f} ms")
print(f"测试集准确率: {accuracy * 100:.2f}%")

# 5. 可视化生成
# 绘制 Loss 曲线
plt.figure(figsize=(6, 4))
plt.plot(range(epochs), loss_history, color='b', linewidth=2)
plt.title('PyTorch MLP Train Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig('mlp_loss_curve.png', dpi=300)
plt.close()

# 绘制决策边界 (降维至花瓣长宽)
X_vis = scaler.fit_transform(df.iloc[:, [2, 3]].values)
model_vis = MLP(input_dim=2).to(device)
opt_vis = optim.Adam(model_vis.parameters(), lr=0.05)
for _ in range(150):
    opt_vis.zero_grad()
    loss = criterion(model_vis(torch.FloatTensor(X_vis).to(device)), torch.FloatTensor(y).view(-1,1).to(device))
    loss.backward()
    opt_vis.step()

x_min, x_max = X_vis[:, 0].min() - 1, X_vis[:, 0].max() + 1
y_min, y_max = X_vis[:, 1].min() - 1, X_vis[:, 1].max() + 1
xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.02), np.arange(y_min, y_max, 0.02))
grid = torch.FloatTensor(np.c_[xx.ravel(), yy.ravel()]).to(device)

model_vis.eval()
with torch.no_grad():
    Z = (model_vis(grid).cpu().numpy() >= 0.5).astype(int).reshape(xx.shape)

plt.figure(figsize=(6, 5))
plt.contourf(xx, yy, Z, alpha=0.3, cmap=ListedColormap(['#FFAAAA', '#AAAAFF']))
plt.scatter(X_vis[:, 0], X_vis[:, 1], c=y, cmap=ListedColormap(['#FF0000', '#0000FF']), edgecolors='k')
plt.title('PyTorch MLP的决策边界图')
plt.xlabel('花瓣长度（Std）')
plt.ylabel('花瓣宽度（Std）')
plt.tight_layout()
plt.savefig('mlp_decision_boundary.png', dpi=300)
plt.close()
print("图像已保存: mlp_loss_curve.png,mlp_decision_boundary.png")