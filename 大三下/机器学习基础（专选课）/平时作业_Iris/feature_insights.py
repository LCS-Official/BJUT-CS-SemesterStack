import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
import xgboost as xgb
import warnings

warnings.filterwarnings("ignore")
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus'] = False 

print("=== 方向三：模型可解释性与特征洞察 ===")

# ==========================================
# 1. 基础数据准备
# ==========================================
features_names = ['Sepal Length', 'Sepal Width', 'Petal Length', 'Petal Width']
df = pd.read_csv('./iris_data.txt', header=None, names=features_names + ['label'])
df = df[df['label'].isin(['Iris-setosa', 'Iris-versicolor'])]
df['label'] = df['label'].map({'Iris-setosa': 0, 'Iris-versicolor': 1})

X = df.iloc[:, :-1].values
y = df.iloc[:, -1].values

# 标准化特征 (这对线性模型的权重对比极其重要！)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ==========================================
# 2. 训练模型并提取特征参数
# ==========================================
# 训练线性模型 (提取 Coef_)
lr_model = LogisticRegression(random_state=42)
svm_model = SVC(kernel='linear', random_state=42)

lr_model.fit(X_scaled, y)
svm_model.fit(X_scaled, y)

lr_coef = lr_model.coef_[0]
svm_coef = svm_model.coef_[0]

# 训练树模型 (提取 Feature Importance)
dt_model = DecisionTreeClassifier(max_depth=3, random_state=42)
xgb_model = xgb.XGBClassifier(n_estimators=50, max_depth=3, eval_metric='logloss', random_state=42)

dt_model.fit(X_scaled, y)
xgb_model.fit(X_scaled, y)

dt_importance = dt_model.feature_importances_
xgb_importance = xgb_model.feature_importances_

# ==========================================
# 3. 绘制并排双图进行对比
# ==========================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
x_indexes = np.arange(len(features_names))
width = 0.35

# 图 1：线性模型的特征权重 (允许有负数，代表负相关)
ax1.bar(x_indexes - width/2, lr_coef, width, label='Logistic Regression', color='#4C72B0')
ax1.bar(x_indexes + width/2, svm_coef, width, label='Linear SVM', color='#DD8452')
ax1.set_title('线性模型: 特征权重')
ax1.set_xticks(x_indexes)
ax1.set_xticklabels(features_names)
ax1.set_ylabel('权重值')
ax1.axhline(0, color='black', linewidth=1.2) # 画一条0刻度基准线
ax1.legend()
ax1.grid(True, axis='y', linestyle='--', alpha=0.6)

# 图 2：集成/树模型的特征重要性 (全是正数，总和为1)
ax2.bar(x_indexes - width/2, dt_importance, width, label='Decision Tree', color='#55A868')
ax2.bar(x_indexes + width/2, xgb_importance, width, label='XGBoost', color='#C44E52')
ax2.set_title('树模型: 特征重要性')
ax2.set_xticks(x_indexes)
ax2.set_xticklabels(features_names)
ax2.set_ylabel('重要性分数 (0.0~1.0)')
ax2.legend()
ax2.grid(True, axis='y', linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('feature_insights.png', dpi=300)
print(">>> 运行完毕！特征解释图已保存为 feature_insights.png")