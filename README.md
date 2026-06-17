# koko-qmt

本项目是一个基于 Python + FastAPI + PostgreSQL + Streamlit + 国金证券 QMT / XtQuant 的本地量化交易平台。

核心目标：

1. 本地连接 QMT 客户端。
2. 同步 A 股 / ETF 行情数据到 PostgreSQL。
3. 实现 ETF 轮动、T0、打板分析、期货套利等策略模块。
4. 提供模拟盘和实盘半自动一键调仓功能。
5. 实盘交易必须经过风控和人工确认。

开发顺序：

1. 项目骨架与规则
2. QMT 连接管理
3. PostgreSQL 数据中心
4. 行情增量同步
5. 策略引擎
6. 模拟盘
7. 实盘预案与半自动下单
8. Streamlit 前端
9. 日志、风控、测试与打包
