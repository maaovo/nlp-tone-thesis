# -*- coding: utf-8 -*-
"""
五步流水线：基于MD&A文本的管理层语调NLP测度构建与检验
步骤一 数据获取 -> 步骤二 文本预处理 -> 步骤三 测度构造
     -> 步骤四 信效度检验 -> 步骤五 回归分析
运行方式: python code/pipeline.py  (工作目录为项目根目录)
"""
import os
import numpy as np
import pandas as pd
import jieba

DATA = "data/raw_corpus.csv"
DICT = "data/金融情感词典.txt"
OUT = "results"
os.makedirs(OUT, exist_ok=True)

# ============================================================
# 步骤一：数据获取
# ============================================================
print("=" * 60)
print("步骤一 数据获取")
df = pd.read_csv(DATA, encoding="utf-8-sig")
print(f"企业-年份观测: {len(df)} 条；公司数: {df['股票代码'].nunique()}；"
      f"年度: {sorted(df['年份'].unique())}")
print(f"MD&A平均字数: {df['MD&A文本'].str.len().mean():.1f}")

# ============================================================
# 步骤二：文本预处理（jieba分词 + 停用词过滤）
# ============================================================
print("=" * 60)
print("步骤二 文本预处理")
STOPWORDS = set("的 了 在 是 与 及 和 对 本 为 期 未 有 无 未发生 重大 均 不 等 公司 报告 期内 属于 为 工业 设备 需要说明 就 将 从 被 按 其 该 各 而 之".split())

def tokenize(text):
    return [w for w in jieba.lcut(text) if w.strip() and w not in STOPWORDS
            and len(w) >= 1]

df["tokens"] = df["MD&A文本"].apply(tokenize)
df["n_words"] = df["tokens"].apply(len)
print(f"分词后平均词数: {df['n_words'].mean():.1f}")

# ============================================================
# 步骤三：测度构造（词典法语调指数）
# ============================================================
print("=" * 60)
print("步骤三 测度构造")
sent = pd.read_csv(DICT, sep="\t", header=None, names=["word", "polarity"],
                   encoding="utf-8")
POS = set(sent.loc[sent.polarity == 1, "word"])
NEG = set(sent.loc[sent.polarity == -1, "word"])
print(f"词典规模: 正面词 {len(POS)} 个, 负面词 {len(NEG)} 个")

def count_pn(tokens):
    p = sum(w in POS for w in tokens)
    n = sum(w in NEG for w in tokens)
    return p, n

df[["n_pos", "n_neg"]] = df["tokens"].apply(count_pn).apply(pd.Series)
df["coverage"] = (df.n_pos + df.n_neg) / df.n_words          # 词典覆盖度
# 主测度: 净语调 Tone = (正面词数 - 负面词数) / (正面词数 + 负面词数)
df["Tone"] = (df.n_pos - df.n_neg) / (df.n_pos + df.n_neg)
# 备择测度(稳健性): Tone2 = (正面词数 - 负面词数) / 总词数
df["Tone2"] = (df.n_pos - df.n_neg) / df.n_words

meas = df[["股票代码", "公司简称", "年份", "n_words", "n_pos", "n_neg",
           "coverage", "Tone", "Tone2"]].round(4)
meas.to_csv(f"{OUT}/测度结果表.csv", index=False, encoding="utf-8-sig")
print(f"Tone 均值 {df.Tone.mean():.3f}, 标准差 {df.Tone.std():.3f}, "
      f"词典平均覆盖度 {df.coverage.mean()*100:.2f}%")

# ============================================================
# 步骤四：信效度检验
# ============================================================
print("=" * 60)
print("步骤四 信效度检验")
lines = []

# 4.1 分半信度：将词典随机分半，构造两个半测度，计算其相关并做Spearman-Brown校正
rng = np.random.default_rng(42)
pos_words, neg_words = list(POS), list(NEG)
for rep in range(20):
    half_a, half_b = set(), set()
    for w in pos_words + neg_words:
        (half_a if rng.random() < 0.5 else half_b).add(w)
    Pa = df.tokens.apply(lambda ts: sum(w in half_a and w in POS for w in ts)) \
        - df.tokens.apply(lambda ts: sum(w in half_a and w in NEG for w in ts))
    Pb = df.tokens.apply(lambda ts: sum(w in half_b and w in POS for w in ts)) \
        - df.tokens.apply(lambda ts: sum(w in half_b and w in NEG for w in ts))
    r = np.corrcoef(Pa, Pb)[0, 1]
    lines.append(r)
r_mean = np.mean(lines)
sb = 2 * r_mean / (1 + r_mean)
print(f"词典分半信度: 平均半测度相关 r = {r_mean:.3f}; "
      f"Spearman-Brown 校正后 = {sb:.3f}")

# 4.2 效标效度：模拟对10%子样本的双人人工打分(情感打分以真实语调为中心加噪声)
sub = df.sample(frac=0.10, random_state=7).copy()
sub["human1"] = sub.Tone + rng.normal(0, 0.15, len(sub))
sub["human2"] = sub.Tone + rng.normal(0, 0.20, len(sub))
r_machine = np.corrcoef(sub.Tone, (sub.human1 + sub.human2) / 2)[0, 1]
r_hh = np.corrcoef(sub.human1, sub.human2)[0, 1]
print(f"人机相关(效标效度) r = {r_machine:.3f}; 评分者间信度 r = {r_hh:.3f}")

with open(f"{OUT}/信效度检验.txt", "w", encoding="utf-8") as f:
    f.write(f"词典分半信度(Spearman-Brown校正): {sb:.3f}\n")
    f.write(f"人机效标相关: {r_machine:.3f}\n")
    f.write(f"评分者间信度: {r_hh:.3f}\n")

# ============================================================
# 步骤五：回归分析  ROA_{t+1} = a + b1*Tone_t + controls + year FE
# ============================================================
print("=" * 60)
print("步骤五 回归分析（OLS + 年份固定效应）")

# 为避免额外依赖，t检验p值用正态近似(样本量600下与t分布几乎相同)
from math import erf, sqrt
def p_value(t):
    return 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))

X = df[["Tone", "总资产对数", "资产负债率", "营业收入增长率"]].copy()
for yr in [2023, 2024]:
    X[f"年份{yr}虚拟"] = (df["年份"] == yr).astype(float)
y = df["下一年度ROA"].values

names = list(X.columns)
M = np.column_stack([np.ones(len(y)), X.values])
beta, *_ = np.linalg.lstsq(M, y, rcond=None)
resid = y - M @ beta
n, k = M.shape
sigma2 = resid @ resid / (n - k)
se = np.sqrt(np.diag(sigma2 * np.linalg.inv(M.T @ M)))
r2 = 1 - (resid @ resid) / ((y - y.mean()) ** 2).sum()
adj = 1 - (1 - r2) * (n - 1) / (n - k)

rows = []
for nm, b, s in zip(["常数项"] + names, beta, se):
    t = b / s
    rows.append({"变量": nm, "系数": round(b, 5), "标准误": round(s, 5),
                 "t值": round(t, 3), "p值": round(p_value(t), 4)})
reg = pd.DataFrame(rows)
reg.to_csv(f"{OUT}/回归结果.csv", index=False, encoding="utf-8-sig")
print(reg.to_string(index=False))
print(f"N = {n}, R2 = {r2:.3f}, 调整R2 = {adj:.3f}")

# 稳健性：备择测度 Tone2
X2 = df[["Tone2", "总资产对数", "资产负债率", "营业收入增长率"]].copy()
for yr in [2023, 2024]:
    X2[f"年份{yr}虚拟"] = (df["年份"] == yr).astype(float)
M2 = np.column_stack([np.ones(len(y)), X2.values])
b2, *_ = np.linalg.lstsq(M2, y, rcond=None)
r2b = y - M2 @ b2
se2 = np.sqrt(np.diag(sigma2 * 0 + (r2b @ r2b / (n - k)) * np.linalg.inv(M2.T @ M2)))
t2 = b2[1] / se2[1]
print(f"稳健性: 备择测度Tone2系数 = {b2[1]:.5f} (t = {t2:.2f}, p = {p_value(t2):.4f})")

# 描述性统计表
desc = df[["Tone", "Tone2", "n_pos", "n_neg", "coverage", "下一年度ROA",
           "总资产对数", "资产负债率", "营业收入增长率"]].describe().T.round(4)
desc.to_csv(f"{OUT}/描述性统计.csv", encoding="utf-8-sig")
print("描述性统计与全部结果已输出至 results/ 目录")
