# koko-qmt Backend PRD

## 1. 项目定位

koko-qmt 是一个本地量化交易平台后端，专注于：

- 高并发行情数据处理
- 本地 PostgreSQL 数据中心
- ETF 轮动策略
- T0 信号策略
- 打板分析
- 期货跨期套利分析
- 模拟盘
- 实盘半自动一键调仓

核心运行环境为 Windows，因为国金证券 QMT 和 XtQuant 依赖 Windows 本地客户端。

## 2. 后端架构

后端使用 FastAPI。

核心模块：

- QmtConnectionManager：QMT 连接管理
- DataSyncEngine：行情数据同步
- StrategyEngine：策略引擎
- SignalGenerator：信号生成器
- PaperTradingEngine：模拟盘
- RebalanceRouter：调仓预案路由
- TradingExecutor：实盘交易执行
- RiskManager：风控
- LimitUpAnalyzer：打板分析
- FutureArbitrageEngine：期货套利扫描
- LoggingManager：日志系统

## 3. QMT 连接管理

要求：

- 全局单例连接
- 支持 mock 模式
- 支持真实 xtquant 模式
- 支持连接测试
- 支持查询资金账号
- 支持查询持仓
- 支持查询资产
- 支持订阅行情
- 支持下单和撤单封装

## 4. 数据中心

数据库使用 PostgreSQL。

核心数据：

- 证券基础信息
- 日线行情
- 分钟线行情，后续实现
- 策略信号
- 模拟盘持仓
- 模拟盘成交
- 实盘订单
- 审计日志

要求：

- 支持增量同步
- 支持批量写入
- 支持冲突忽略
- 支持同步进度查询
- 不阻塞 FastAPI 主线程

## 5. ETF 轮动策略

第一版只做简单可验证版本：

- 读取 ETF 池
- 计算 10 日、20 日、60 日动量
- 得分 = 0.4 * R10 + 0.3 * R20 + 0.3 * R60
- 选择得分最高且大于 0 的 Top N
- 生成 BUY / SELL / HOLD 信号
- 写入 strategy_signals 表

## 6. 实盘交易

实盘交易分两步：

第一步：生成交易预案。

- 读取策略目标持仓
- 读取真实账户持仓
- 计算差额
- 生成买入 / 卖出预案
- 返回给前端展示

第二步：人工确认后执行。

- ENABLE_REAL_TRADE 必须为 true
- 前端必须传 confirm=true
- 后端先执行卖出
- 等待卖出结果
- 再执行买入
- 每一笔订单写入 real_trade_orders
- 每一步写入 trade_audit_logs

## 7. 风控要求

必须内置：

- 单笔订单不超过总资产 30%
- 禁止无确认实盘下单
- QMT 断线时禁止实盘下单
- 柜台错误 1 分钟 3 次后熔断
- 资金不足直接拒单
- 废单必须记录
- 所有真实交易必须审计

## 8. 前端要求

前端使用 Streamlit。

页面包括：

- 数据中心
- 策略管理
- ETF 轮动
- 模拟交易
- 实盘交易
- T0 信号
- 打板分析
- 期货套利
- 系统日志

前端不能直接调用 xtquant，只能调用 FastAPI。

## 9. 当前开发原则

先实现可运行 MVP，不追求一次性全功能。

MVP 顺序：

1. FastAPI 能启动
2. health 接口正常
3. QMT mock 连接正常
4. PostgreSQL 表能创建
5. 数据同步接口能返回 mock 进度
6. ETF 轮动能跑 mock 数据
7. 交易预案能生成
8. Streamlit 能展示
9. 最后再接真实 xtquant
