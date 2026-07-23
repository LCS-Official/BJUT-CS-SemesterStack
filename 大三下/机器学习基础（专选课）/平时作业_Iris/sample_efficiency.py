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
import warnings
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus'] = False 

# 忽略极小样本下的一些无害警告
warnings.filterwarnings("ignore")

print("=== 六大模型：样本效率 (Sample Efficiency) 极限测试 ===")

# ==========================================
# 1. 基础数据准备 (严格遵守二分类)
# ==========================================
columns = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'label']
df = pd.read_csv('./iris_data.txt', header=None, names=columns)
df = df[df['label'].isin(['Iris-setosa', 'Iris-versicolor'])]
df['label'] = df['label'].map({'Iris-setosa': 0, 'Iris-versicolor': 1})

X = df.iloc[:, :-1].values
y = df.iloc[:, -1].values
device = torch.device("xpu" if torch.xpu.is_available() else "cpu")

# 划分出基础的 80% 训练集和 20% 测试集
X_tr_base, X_te_base, y_tr_base, y_te_base = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
scaler = StandardScaler()
X_tr_base = scaler.fit_transform(X_tr_base)
X_te_base = scaler.transform(X_te_base)

# ==========================================
# 2. 核心实验设计：控制训练数据喂入比例
# ==========================================
# 5%的比例意味着我们只给模型 4条 数据 (2条0类，2条1类)
fractions = [0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
n_repeats = 20 # 为消除极小样本的偶然性，每个比例下重复实验20次取平均

model_names = ["Logistic Regression", "Linear SVM", "Decision Tree", "Gaussian NB", "XGBoost", "PyTorch MLP"]
results_acc = {name: [] for name in model_names}

for frac in fractions:
    frac_accs = {name: [] for name in model_names}
    
    for seed in range(n_repeats):
        # 按比例抽取“子训练集”
        if frac == 1.0:
            X_tr_sub, y_tr_sub = X_tr_base, y_tr_base
        else:
            X_tr_sub, _, y_tr_sub, _ = train_test_split(
                X_tr_base, y_tr_base, train_size=frac, random_state=seed, stratify=y_tr_base
            )
        
        # 定义传统模型
        models = {
            "Logistic Regression": LogisticRegression(random_state=seed),
            "Linear SVM": SVC(kernel='linear', random_state=seed),
            "Decision Tree": DecisionTreeClassifier(max_depth=3, random_state=seed),
            "Gaussian NB": GaussianNB(),
            "XGBoost": xgb.XGBClassifier(n_estimators=50, max_depth=3, eval_metric='logloss', random_state=seed)
        }
        
        # 训练传统模型并记录测试集准确率
        for name, model in models.items():
            model.fit(X_tr_sub, y_tr_sub)
            frac_accs[name].append(accuracy_score(y_te_base, model.predict(X_te_base)))
            
        # 训练 PyTorch 神经网络
        model_mlp = nn.Sequential(nn.Linear(4, 16), nn.ReLU(), nn.Linear(16, 1), nn.Sigmoid()).to(device)
        optimizer = optim.Adam(model_mlp.parameters(), lr=0.05)
        criterion = nn.BCELoss()
        X_t = torch.FloatTensor(X_tr_sub).to(device)
        y_t = torch.FloatTensor(y_tr_sub).view(-1, 1).to(device)
        
        for _ in range(120): # 小样本训练 120 轮
            optimizer.zero_grad()
            loss = criterion(model_mlp(X_t), y_t)
            loss.backward()
            optimizer.step()
            
        with torch.no_grad():
            X_te_t = torch.FloatTensor(X_te_base).to(device)
            preds = (model_mlp(X_te_t).cpu().numpy() >= 0.5).astype(int).flatten()
            frac_accs["PyTorch MLP"].append(accuracy_score(y_te_base, preds))
            
    # 计算当前比例下的平均准确率
    for name in model_names:
        results_acc[name].append(np.mean(frac_accs[name]))
    print(f"[*] 训练数据馈入量 {frac*100:3.0f}% (样本数: {len(y_tr_sub)}) --> 评测完成")

# ==========================================
# 3. 结果可视化
# ==========================================
plt.figure(figsize=(10, 6))
markers = ['o', 's', '^', 'D', 'v', 'p']

for (name, accs), marker in zip(results_acc.items(), markers):
    # 将最具对比性的 高斯朴素贝叶斯 和 神经网络 加粗展示
    lw = 3 if name in ["PyTorch MLP", "Gaussian NB"] else 1.5
    alpha = 1.0 if name in ["PyTorch MLP", "Gaussian NB"] else 0.5
    plt.plot(fractions, accs, marker=marker, label=name, linewidth=lw, alpha=alpha)

plt.title('样本效率：测试准确率和训练集比例关系')
plt.xlabel('测试集划分比例（1.0为全部80条数据）')
plt.ylabel('平均测试准确率')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig('sample_efficiency.png', dpi=300)
print("\n>>> 运行完毕！图表已保存为 sample_efficiency.png")