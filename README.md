# 管理层语调的NLP测度构建及其对企业未来业绩的预测力研究

> 毕业论文（预演）模拟稿 | 基于A股上市公司年报MD&A文本的"NLP测度构建五步流水线"完整实证演示

## 研究简介

本项目完整示范一条 **NLP 测度构建五步流水线**，并把全部材料（论文、代码、测度结果、数据说明）公开：

```
步骤一 数据获取 → 步骤二 文本预处理 → 步骤三 测度构造 → 步骤四 信效度检验 → 步骤五 回归分析
```

- **研究对象**：200家A股上市公司 2022—2024 年年报"管理层讨论与分析"(MD&A)文本，共 600 个企业—年份观测
- **核心测度**：净语调指数 `Tone = (正面词数 − 负面词数) / (正面词数 + 负面词数)`（73词中文金融情感词典）
- **信效度检验**：词典分半信度（Spearman-Brown 校正）= 0.820；人机效标相关 = 0.951；评分者间信度 = 0.843
- **核心发现**：控制规模、杠杆、成长性与年份固定效应后，当期语调对下一年度 ROA 的预测系数为 0.049（t=21.71, p<0.001）；备择测度 Tone2 结果稳健

## 一键复现

```bash
pip install jieba pandas numpy
python data/generate_corpus.py   # 生成模拟语料（真实研究中替换为巨潮资讯网年报解析结果）
python code/pipeline.py          # 五步流水线，输出全部结果至 results/
python code/make_docx.py         # 可选：重新生成 Word 版论文
```

## 上传到 GitHub（github.com 无法直连时）

```bash
# 1. 生成令牌：https://github.com/settings/tokens （勾选 repo 权限）
# 2. 设置环境变量后运行，脚本会自动建仓并上传全部文件（走官方 api.github.com）
$env:GITHUB_TOKEN="ghp_xxxx"; python code/push_via_api.py
```

## 仓库结构

```
├── thesis/
│   ├── 毕业论文模拟稿.md      # 论文全文（Markdown版，约6900汉字）
│   └── 毕业论文模拟稿.docx    # 论文全文（Word版，含封面、目录）
├── code/
│   ├── pipeline.py            # 五步流水线主程序（数据获取→预处理→测度→信效度→回归）
│   └── make_docx.py           # Word版论文生成脚本
├── data/
│   ├── generate_corpus.py     # 模拟语料生成脚本
│   ├── raw_corpus.csv         # 原始语料面板（600条 企业-年份）
│   └── 金融情感词典.txt        # 中文金融情感词典（正面39词/负面34词）
└── results/
    ├── 测度结果表.csv          # 企业-年份语调测度面板（流水线步骤三输出）
    ├── 描述性统计.csv          # 主要变量描述性统计
    ├── 信效度检验.txt          # 分半信度/效标效度/评分者间信度
    └── 回归结果.csv            # 回归系数表（步骤五输出）
```

## 数据来源说明

| 文件 | 来源 | 处理步骤 |
|---|---|---|
| `data/raw_corpus.csv` | 真实研究场景：巨潮资讯网(cninfo.com.cn)年报PDF解析MD&A章节 + CSMAR财务数据；本作业为方法学演示，由 `generate_corpus.py` 按相同统计结构**模拟生成** | 运行生成脚本即可获得，保证零成本一键复现 |
| `data/金融情感词典.txt` | 参照 Loughran & McDonald (2011) 金融语境原则与中文金融情感词典（姚加权等, 2021）思路人工编制 | 词目筛选遵循金融语境特异性原则 |
| `results/*.csv,txt` | 由 `code/pipeline.py` 流水线自动产出 | `python code/pipeline.py` 一键复现 |

> 注：因课程作业条件限制使用模拟语料，具体系数不可外推至真实市场；将 `raw_corpus.csv` 替换为真实数据后，流水线其余步骤无需修改。

## 参考文献（部分）

- Loughran, T., & McDonald, B. (2011). When Is a Liability Not a Liability? *Journal of Finance*, 66(1), 35-65.
- Tetlock, P. C., et al. (2008). More Than Words. *Journal of Finance*, 63(3), 1437-1467.
- 谢德仁, 林乐. (2015). 管理层语调能预示公司未来业绩吗？ *会计研究*(2).
- 胡楠, 等. (2021). 管理层短视主义影响企业长期投资吗？ *管理世界*(5).
- 姚加权, 等. (2021). 语调、情绪及市场影响：基于金融情绪词典的研究. *管理科学学报*, 24(1).

完整参考文献见 `thesis/毕业论文模拟稿.md`。
