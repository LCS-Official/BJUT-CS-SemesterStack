import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
import xgboost as xgb
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus'] = False 

print("=== 六大模型决策边界全家福 ===")

# 1. 数据准备 (只取花瓣长度和宽度用于2D可视化)
columns = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'label']
df = pd.read_csv('./iris_data.txt', header=None, names=columns)
df = df[df['label'].isin(['Iris-setosa', 'Iris-versicolor'])]
df['label'] = df['label'].map({'Iris-setosa': 0, 'Iris-versicolor': 1})

X = df.iloc[:, [2, 3]].values # 只取 petal_length, petal_width
y = df.iloc[:, -1].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 2. 初始化 6 大模型
models = {
    "Logistic Regression": LogisticRegression(random_state=42),
    "Linear SVM": SVC(kernel='linear', random_state=42, probability=True),
    "Decision Tree": DecisionTreeClassifier(max_depth=3, random_state=42),
    "Gaussian Naive Bayes": GaussianNB(),
    "XGBoost": xgb.XGBClassifier(n_estimators=50, max_depth=3, eval_metric='logloss', random_state=42)
}

# 训练 sklearn 和 xgb 模型
for name, model in models.items():
    model.fit(X_scaled, y)

# 单独训练 PyTorch MLP
device = torch.device("xpu" if torch.xpu.is_available() else "cpu")
class MLP(nn.Module):
    def __init__(self):
        super(MLP, self).__init__()
        self.fc1 = nn.Linear(2, 16)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()
    def forward(self, x):
        return self.sigmoid(self.fc2(self.relu(self.fc1(x))))

mlp = MLP().to(device)
optimizer = optim.Adam(mlp.parameters(), lr=0.05)
criterion = nn.BCELoss()
X_tensor = torch.FloatTensor(X_scaled).to(device)
y_tensor = torch.FloatTensor(y).view(-1, 1).to(device)

for _ in range(150):
    optimizer.zero_grad()
    loss = criterion(mlp(X_tensor), y_tensor)
    loss.backward()
    optimizer.step()

# 3. 绘制 2x3 全家福决策边界
x_min, x_max = X_scaled[:, 0].min() - 1, X_scaled[:, 0].max() + 1
y_min, y_max = X_scaled[:, 1].min() - 1, X_scaled[:, 1].max() + 1
xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.02), np.arange(y_min, y_max, 0.02))
grid = np.c_[xx.ravel(), yy.ravel()]

fig, axes = plt.subplots(2, 3, figsize=(15, 9))
cmap_background = ListedColormap(['#FFAAAA', '#AAAAFF'])
cmap_points = ListedColormap(['#FF0000', '#0000FF'])

all_model_names = list(models.keys()) + ["PyTorch MLP"]

for i, ax in enumerate(axes.flatten()):
    name = all_model_names[i]
    if name == "PyTorch MLP":
        mlp.eval()
        with torch.no_grad():
            grid_tensor = torch.FloatTensor(grid).to(device)
            Z = (mlp(grid_tensor).cpu().numpy() >= 0.5).astype(int)
    else:
        Z = models[name].predict(grid)
        
    Z = Z.reshape(xx.shape)
    ax.contourf(xx, yy, Z, alpha=0.3, cmap=cmap_background)
    ax.scatter(X_scaled[:, 0], X_scaled[:, 1], c=y, cmap=cmap_points, edgecolors='k')
    ax.set_title(name)
    ax.set_xlabel('花瓣长度（Std）')
    ax.set_ylabel('花瓣宽度（Std）')

plt.tight_layout()
plt.savefig('all_models_boundaries.png', dpi=300)
print(">>> 已保存: all_models_boundaries.png")