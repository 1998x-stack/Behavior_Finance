# 架构选型与实证方法决策记录（ADR-001）

日期：2026-10-30。本文是 M02–M14 的设计依据，不表示相关功能已经实现。

## 1. 网站栈：内容优先，避免重新造轮子

当前 42 个 HTML 由重复静态模板构成。推荐在 M03 对比 Zensical 与 MkDocs+Material 构建同一套 Markdown 样例，逐项检查中文分词搜索、公式、表格、锚点、导航、离线输出和扩展插件。

- MkDocs：轻量、现有 Python 生态广，但上游维护状况需要特别评估。
- Material for MkDocs：搜索、导航功能完善，官方已经宣布维护至 2027-05-05。
- Zensical：由 Material 团队建设的兼容路线；2026-11-05 计划进入 0.1.0 系列，尚有兼容功能需要实测。
- 结论：M02 先修已有静态页面；M03 同时做双构建器 PoC，锁定版本后选择，禁止无测试的一次性迁移。

来源：https://zensical.org/docs/ ; https://zensical.org/roadmap/ ; https://squidfunk.github.io/mkdocs-material/

## 2. 研究层：先轻量实验，再引入框架

- 行为模型（M06–M08）：Python NumPy/SciPy，实验配置/随机种子/模型假设作为首要版本化实体。
- 市场研究（M09–M10）：Arrow/Parquet 表格式数据、DuckDB / pandas 作为候选，但必须记录披露时点 as-of 与复权规则；依数据规模选型。
- 研究流水线（M11）：可以以 Microsoft Qlib 作为数据/模型/研究工作流的参考基线；官方当前提醒其数据集无法直接依赖，实际接入前必须核对许可证与质量。
- 计算验证（M11）：vectorbt 适合大量向量化策略仿真，但结果的数值正确性与真实可交易性需要独立检验。优先建立小型透明黄金回测，再引入外部引擎。

来源：https://github.com/microsoft/qlib ; https://vectorbt.dev/

## 3. 研究可信度：强制区分四个层次

1) 理论层：心理学效应和描述模型（需原文出处）。
2) 实验层：可复现的人造受试情境（不能自动外推至真实市场）。
3) 实证层：点时市场数据、事前假设、样本外检验、统计不确定性。
4) 策略层：成本、流动性、风险暴露、样本选择与多重搜索后的独立评估。

金融文献反复指出：在大量因子尝试后，未经多重检验修正的统计显著性不可靠；高绩效回测容易因参数搜索产生过拟合。必须记录尝试过的全部变体及失败结果，严禁只展示最佳一次回测。

来源：Harvey, Liu & Zhu (2016), https://doi.org/10.1093/rfs/hhv059 ; Bailey et al. (2015), https://doi.org/10.2139/ssrn.2326253

## 4. 数据质量与独立评测的最小契约

每个研究任务输入应明确：
- dataset_id、schema_version、source/license、as_of_time、frequency、timezone、universe、split_manifest；
- code_revision、model_parameters、seed、training/test separation、cost model；
- baseline、metric definition、confidence intervals、multiple-testing method、known caveats。

独立 evaluator 不读取研究模块缓存结果来假装复算。数值检验应有独立实现或黄金集，LLM 只审查研究描述、引用和可读性。

## 5. 当前阻断事项

- M01：已完成代码及 CI；待合并前审核，真实含 PDF 备份未执行。
- M02：polyfill.io 风险仍在现有发布 HTML 中，需优先修复。
- M03：当前构建栈未统一，不应直接添加后端账户与复杂数据库。
- M04：27 篇课程占位，不能把目录长度当作学习内容完成率。
- M05：原课程 PDF 和新网站公开分发需版权/许可审查。
