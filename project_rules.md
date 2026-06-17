# koko-qmt Project Rules

你是本项目的资深 Python 量化交易系统架构师。

本项目是一个本地化 A 股 / ETF / 期货辅助量化交易平台，技术栈固定为：

- Python 3.10+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Streamlit
- 国金证券 QMT / XtQuant
- Windows 10 / Windows 11 本地运行

## 最高优先级原则

1. 不允许把实盘交易做成默认自动化。
2. 默认交易模式必须是 paper / mock / preview。
3. 任何真实下单前，必须经过：
   - 交易预案生成
   - 风控检查
   - 用户前端二次确认
   - 后端 ENABLE_REAL_TRADE=true 检查
4. QMT / XtQuant 调用必须集中封装在 ackend/services/qmt/ 目录，不允许散落在业务代码里。
5. 数据库读写必须集中在 ackend/db/、ackend/models/、ackend/services/data_center/。
6. 策略逻辑必须集中在 ackend/services/strategy/。
7. 实盘交易路由必须集中在 ackend/services/trading/。
8. 风控逻辑必须集中在 ackend/services/risk/。
9. Streamlit 只做前端展示和按钮触发，不允许直接调用 xtquant。
10. 前端必须通过 FastAPI 调用后端。

## 禁止事项

- 禁止在没有用户明确确认的情况下调用真实买入、卖出接口。
- 禁止把账号、密码、资金账号、Cookie、Token 写死到代码里。
- 禁止大面积重构已经稳定的模块。
- 修 Bug 时，只修改相关函数或相关文件。
- 禁止随意引入未在 requirements.txt 中声明的第三方库。
- 禁止用伪代码替代可运行代码。
- 禁止忽略异常处理和日志记录。

## 代码风格

- 所有核心函数必须有中文注释。
- 所有 API 返回统一 JSON：
  {
    "success": true,
    "message": "说明",
    "data": {}
  }
- 所有异常必须被捕获并写入 error 日志。
- 所有交易相关操作必须写入 trade_audit 日志。
- 所有模块必须支持 mock 模式，方便没有 QMT 环境时开发和测试。

## 后端 API 规划

基础接口：

- GET /api/v1/health
- GET /api/v1/qmt/status
- POST /api/v1/qmt/connect
- POST /api/v1/data/sync/start
- GET /api/v1/data/sync/status
- GET /api/v1/securities
- POST /api/v1/strategy/etf-rotation/run
- GET /api/v1/strategy/signals
- GET /api/v1/trade/preview
- POST /api/v1/trade/execute
- GET /api/v1/account/positions
- GET /api/v1/account/assets
- GET /api/v1/analysis/limit-up
- GET /api/v1/analysis/futures-arbitrage

## 数据库核心表

必须优先实现：

- security_info：证券基础信息
- kline_daily：日线数据
- strategy_signals：策略信号
- paper_positions：模拟盘持仓
- paper_trades：模拟盘成交
- real_trade_orders：实盘委托记录
- trade_audit_logs：交易审计日志
- limit_up_analysis：打板分析结果
- futures_arbitrage_signals：期货套利信号

## 开发顺序

严格按以下顺序开发：

1. FastAPI 基础骨架
2. 配置系统
3. 日志系统
4. QMT 连接管理器，先 mock，后真实 xtquant
5. PostgreSQL 表结构
6. 数据中心增量同步
7. ETF 轮动策略
8. 模拟盘引擎
9. 实盘交易预案
10. 实盘半自动执行
11. Streamlit 前端
12. T0、打板、期货套利扩展模块
13. 测试、异常处理、打包运行脚本

每完成一个阶段，必须提供：

1. 修改了哪些文件
2. 如何运行
3. 如何测试
4. 当前阶段未完成的事项
