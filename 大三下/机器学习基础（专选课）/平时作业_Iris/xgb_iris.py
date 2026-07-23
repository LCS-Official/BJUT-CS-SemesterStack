import time
import numpy as np
import pandas as pd
import xgboost as xgb
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus'] = False 

print("XGBoost集成学习Iris实验")

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

# 2. 模型定义与训练
model = xgb.XGBClassifier(
    n_estimators=50, 
    learning_rate=0.1, 
    max_depth=3, 
    use_label_encoder=False, 
    eval_metric='logloss',
    random_state=42
)

start_time = time.perf_counter()
model.fit(X_train_scaled, y_train)
train_time = (time.perf_counter() - start_time) * 1000

# 3. 模型评估
preds = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, preds)

print(f"训练耗时: {train_time:.2f} ms")
print(f"测试集准确率: {accuracy * 100:.2f}%")

# 4. 可视化生成 (决策边界)
X_vis = scaler.fit_transform(df.iloc[:, [2, 3]].values)
model_vis = xgb.XGBClassifier(n_estimators=50, max_depth=3, eval_metric='logloss')
model_vis.fit(X_vis, y)

x_min, x_max = X_vis[:, 0].min() - 1, X_vis[:, 0].max() + 1
y_min, y_max = X_vis[:, 1].min() - 1, X_vis[:, 1].max() + 1
xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.02), np.arange(y_min, y_max, 0.02))

Z = model_vis.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

plt.figure(figsize=(6, 5))
plt.contourf(xx, yy, Z, alpha=0.3, cmap=ListedColormap(['#FFAAAA', '#AAAAFF']))
plt.scatter(X_vis[:, 0], X_vis[:, 1], c=y, cmap=ListedColormap(['#FF0000', '#0000FF']), edgecolors='k')
plt.title('XGBoost的决策边界图')
plt.xlabel('花瓣长度（Std）')
plt.ylabel('花瓣宽度（Std）')
plt.tight_layout()
plt.savefig('xgb_decision_boundary.png', dpi=300)
plt.close()
print("图像已保存: xgb_decision_boundary.png")