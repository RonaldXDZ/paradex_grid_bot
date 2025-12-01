# Paradex Grid Bot

一个基于 Python 与 CCXT 的 Paradex 网格交易机器人，支持终端仪表盘展示与基础日志记录。项目默认在测试网运行，避免误操作带来资金风险。

## 功能特性
- 使用 CCXT 连接 Paradex，自动加载市场并轮询最新价格
- 网格策略：在设定价格区间内按等距价格触发买卖挂单（可干跑）
- 终端仪表盘：实时显示当前价格、动作、日志尾部
- 状态持久化：在 `logs/state.json` 保存已触发的网格点位
- 安全默认：`.env` 不入库，`logs/` 与缓存文件被 `.gitignore` 忽略

## 目录结构
```
paradex_grid_bot/
├─ paradex_grid_bot.py   # 网格机器人主程序
├─ dashboard.py          # 终端仪表盘
├─ requirements.txt      # 依赖
├─ .env                  # 环境变量（本地保存、不会被提交）
├─ .gitignore            # 忽略规则
└─ logs/                 # 日志与状态文件
```

## 快速开始
1) 安装依赖
```bash
python -m pip install -r requirements.txt
```

2) 配置环境变量（创建并编辑 `.env`）
```ini
PARADEX_API_KEY=your_api_key_here
PARADEX_API_SECRET=your_api_secret_here
NETWORK=testnet            # mainnet/testnet，默认 testnet
SYMBOL=ETH/USDC            # 交易对
GRID_LOWER=3500            # 网格下边界
GRID_UPPER=4000            # 网格上边界
GRID_LINES=10              # 网格条数（等距）
GRID_QUANTITY=0.001        # 每次下单数量
POLL_INTERVAL=2.0          # 轮询间隔（秒）
DRY_RUN=true               # 干跑模式（不真实下单）
```

3) 运行机器人与仪表盘
```bash
python paradex_grid_bot.py
python dashboard.py
```

## 参数说明
- `NETWORK`：尝试启用 CCXT 的沙盒/测试网模式；主网请设为 `mainnet`
- `DRY_RUN`：为 `true/1/yes` 时仅打印下单动作，不发单
- `GRID_LINES`：等距划分为若干价格层；价格低于层位触发买，高于层位触发卖
- `SYMBOL`：请确保该交易对在 Paradex 可用

## 日志与状态
- 日志文件：`logs/grid_bot.log`
- 状态文件：`logs/state.json`（记录已触发的买/卖层位与网格配置）

## 风险声明
- 交易有风险，策略示例仅供学习参考。务必在 `testnet` 验证策略，谨慎切换主网。
- 请妥善管理私钥与 API 凭证；`.env` 已在 `.gitignore` 中忽略，勿将密钥写入代码或提交到仓库。

## 实现说明
- 交易所接入通过 `ccxt.paradex`，启用速率限制并加载市场
- 策略逻辑位于 `paradex_grid_bot.py`，等距价格栅格由 `numpy.linspace` 生成
- 终端 UI 使用 `rich`，日志使用标准 `logging`

## 许可
本项目用于教学演示，不附带任何担保。你可按自身需求进行修改与扩展。
