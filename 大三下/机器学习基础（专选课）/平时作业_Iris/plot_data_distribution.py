import os
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# 1. 基础设置
# =========================

DATA_PATH = "./iris_data.txt"
OUT_DIR = "./figures_data_distribution"
os.makedirs(OUT_DIR, exist_ok=True)

# 尽量解决中文显示问题
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# Iris 数据列名
columns = [
    "Sepal Length",
    "Sepal Width",
    "Petal Length",
    "Petal Width",
    "Species"
]

# 读取数据
df = pd.read_csv(DATA_PATH, header=None, names=columns)

# 本次实验只取前两类：Setosa 和 Versicolor
binary_df = df[df["Species"].isin(["Iris-setosa", "Iris-versicolor"])].copy()

# 标签简化，方便图上显示
binary_df["Species Short"] = binary_df["Species"].replace({
    "Iris-setosa": "Setosa",
    "Iris-versicolor": "Versicolor"
})

print("原始数据集大小：", df.shape)
print("二分类数据集大小：", binary_df.shape)
print("\n二分类类别数量：")
print(binary_df["Species Short"].value_counts())

# =========================
# 2. 图1：二分类类别数量柱状图
# =========================

counts = binary_df["Species Short"].value_counts().reindex(["Setosa", "Versicolor"])

plt.figure(figsize=(6, 4))
plt.bar(counts.index, counts.values)
plt.title("二分类数据集类别数量分布")
plt.xlabel("类别")
plt.ylabel("样本数量")

for i, v in enumerate(counts.values):
    plt.text(i, v + 1, str(v), ha="center", fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "图1_二分类类别数量分布.png"), dpi=300)
plt.close()

# =========================
# 3. 图2：萼片特征空间 vs 花瓣特征空间散点图
# =========================

plt.figure(figsize=(12, 5))

# 左图：萼片空间
plt.subplot(1, 2, 1)
for species in ["Setosa", "Versicolor"]:
    sub = binary_df[binary_df["Species Short"] == species]
    plt.scatter(
        sub["Sepal Length"],
        sub["Sepal Width"],
        label=species,
        edgecolors="black",
        alpha=0.8
    )

plt.title("萼片特征空间分布")
plt.xlabel("Sepal Length")
plt.ylabel("Sepal Width")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.4)

# 右图：花瓣空间
plt.subplot(1, 2, 2)
for species in ["Setosa", "Versicolor"]:
    sub = binary_df[binary_df["Species Short"] == species]
    plt.scatter(
        sub["Petal Length"],
        sub["Petal Width"],
        label=species,
        edgecolors="black",
        alpha=0.8
    )

plt.title("花瓣特征空间分布")
plt.xlabel("Petal Length")
plt.ylabel("Petal Width")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.4)

plt.suptitle("Setosa与Versicolor在不同特征空间中的分布对比", fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "图2_萼片与花瓣特征空间分布对比.png"), dpi=300)
plt.close()

# =========================
# 4. 图3：四个特征的类别均值对比
# =========================

feature_cols = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]
mean_df = binary_df.groupby("Species Short")[feature_cols].mean().reindex(["Setosa", "Versicolor"])

x = range(len(feature_cols))
bar_width = 0.35

plt.figure(figsize=(9, 5))
plt.bar(
    [i - bar_width / 2 for i in x],
    mean_df.loc["Setosa"],
    width=bar_width,
    label="Setosa"
)
plt.bar(
    [i + bar_width / 2 for i in x],
    mean_df.loc["Versicolor"],
    width=bar_width,
    label="Versicolor"
)

plt.xticks(list(x), feature_cols)
plt.ylabel("平均值")
plt.title("Setosa与Versicolor四个特征均值对比")
plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.4)

for i, value in enumerate(mean_df.loc["Setosa"]):
    plt.text(i - bar_width / 2, value + 0.05, f"{value:.2f}", ha="center", fontsize=8)

for i, value in enumerate(mean_df.loc["Versicolor"]):
    plt.text(i + bar_width / 2, value + 0.05, f"{value:.2f}", ha="center", fontsize=8)

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "图3_四个特征均值对比.png"), dpi=300)
plt.close()

# =========================
# 5. 图4：四个特征箱线图
# =========================

plt.figure(figsize=(12, 8))

for idx, feature in enumerate(feature_cols, start=1):
    plt.subplot(2, 2, idx)

    data_to_plot = [
        binary_df[binary_df["Species Short"] == "Setosa"][feature],
        binary_df[binary_df["Species Short"] == "Versicolor"][feature]
    ]

    plt.boxplot(
        data_to_plot,
        labels=["Setosa", "Versicolor"],
        patch_artist=True
    )

    plt.title(f"{feature} 分布箱线图")
    plt.ylabel(feature)
    plt.grid(axis="y", linestyle="--", alpha=0.4)

plt.suptitle("Setosa与Versicolor四个特征分布对比", fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "图4_四个特征箱线图.png"), dpi=300)
plt.close()

# =========================
# 6. 图5：所有特征两两关系散点矩阵
# =========================

fig, axes = plt.subplots(4, 4, figsize=(12, 12))

for i, y_feature in enumerate(feature_cols):
    for j, x_feature in enumerate(feature_cols):
        ax = axes[i, j]

        if i == j:
            # 对角线画直方图
            for species in ["Setosa", "Versicolor"]:
                sub = binary_df[binary_df["Species Short"] == species]
                ax.hist(
                    sub[x_feature],
                    alpha=0.6,
                    bins=10,
                    label=species
                )
        else:
            # 非对角线画散点图
            for species in ["Setosa", "Versicolor"]:
                sub = binary_df[binary_df["Species Short"] == species]
                ax.scatter(
                    sub[x_feature],
                    sub[y_feature],
                    alpha=0.7,
                    edgecolors="black",
                    s=25
                )

        if i == 3:
            ax.set_xlabel(x_feature, fontsize=9)
        else:
            ax.set_xticklabels([])

        if j == 0:
            ax.set_ylabel(y_feature, fontsize=9)
        else:
            ax.set_yticklabels([])

        ax.grid(True, linestyle="--", alpha=0.25)

# 只放一个统一图例
handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper right")

plt.suptitle("二分类Iris数据四个特征两两关系散点矩阵", fontsize=15)
plt.tight_layout(rect=[0, 0, 0.96, 0.96])
plt.savefig(os.path.join(OUT_DIR, "图5_四个特征两两关系散点矩阵.png"), dpi=300)
plt.close()

# =========================
# 7. 导出统计表，方便写报告
# =========================

desc_table = binary_df.groupby("Species Short")[feature_cols].agg(["mean", "std", "min", "max"])
desc_table.to_excel(os.path.join(OUT_DIR, "二分类数据特征统计表.xlsx"))

print("\n图片已生成到：", OUT_DIR)
print("同时已导出统计表：二分类数据特征统计表.xlsx")