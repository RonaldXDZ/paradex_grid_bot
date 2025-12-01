import os
import time
import json
from pathlib import Path
import ccxt
import numpy as np
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich import box
import logging

console = Console()

def ensure_logs_dir():
    Path("logs").mkdir(parents=True, exist_ok=True)

def setup_logging():
    ensure_logs_dir()
    logger = logging.getLogger("grid_bot")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("logs/grid_bot.log", encoding="utf-8")
    fh.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh.setFormatter(fmt)
    if not logger.handlers:
        logger.addHandler(fh)
    return logger

def read_env():
    load_dotenv()
    api_key = os.getenv("PARADEX_API_KEY", "")
    api_secret = os.getenv("PARADEX_API_SECRET", "")
    network = os.getenv("NETWORK", "testnet").lower()
    symbol = os.getenv("SYMBOL", "ETH/USDC")
    lower = float(os.getenv("GRID_LOWER", "3500"))
    upper = float(os.getenv("GRID_UPPER", "4000"))
    lines = int(os.getenv("GRID_LINES", "10"))
    qty = float(os.getenv("GRID_QUANTITY", "0.001"))
    poll = float(os.getenv("POLL_INTERVAL", "2.0"))
    dry_run = os.getenv("DRY_RUN", "true").strip().lower() in {"1", "true", "yes"}
    return {
        "api_key": api_key,
        "api_secret": api_secret,
        "network": network,
        "symbol": symbol,
        "lower": lower,
        "upper": upper,
        "lines": lines,
        "qty": qty,
        "poll": poll,
        "dry_run": dry_run,
    }

def setup_exchange(api_key: str, api_secret: str, network: str):
    params = {"apiKey": api_key, "secret": api_secret, "enableRateLimit": True}
    exchange = ccxt.paradex(params)
    try:
        exchange.set_sandbox_mode(network == "testnet")
    except Exception:
        pass
    exchange.load_markets()
    return exchange

class GridBot:
    def __init__(self, exchange, symbol, lower, upper, lines, qty, dry_run, logger):
        self.exchange = exchange
        self.symbol = symbol
        self.lower = lower
        self.upper = upper
        self.lines = lines
        self.qty = qty
        self.dry_run = dry_run
        self.logger = logger
        self.levels = list(np.linspace(lower, upper, lines))
        self.state_path = Path("logs/state.json")
        self.filled_buys = set()
        self.filled_sells = set()
        self._load_state()

    def _load_state(self):
        try:
            if self.state_path.exists():
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                self.filled_buys = set(data.get("filled_buys", []))
                self.filled_sells = set(data.get("filled_sells", []))
        except Exception:
            pass

    def _save_state(self):
        try:
            data = {
                "filled_buys": list(self.filled_buys),
                "filled_sells": list(self.filled_sells),
                "levels": self.levels,
                "symbol": self.symbol,
            }
            self.state_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def price(self):
        t = self.exchange.fetch_ticker(self.symbol)
        v = t.get("last") or t.get("close") or t.get("bid") or t.get("ask")
        return float(v)

    def place(self, side: str, price: float):
        if self.dry_run:
            self.logger.info(f"DRY_RUN create {side} {self.qty} {self.symbol} @ {price}")
            return None
        try:
            order = self.exchange.create_order(self.symbol, "limit", side, self.qty, price, {})
            self.logger.info(f"ORDER {order}")
            return order
        except Exception as e:
            self.logger.error(f"ORDER_ERROR {side} {price} {e}")
            return None

    def step(self):
        p = self.price()
        actions = []
        for lv in self.levels:
            if p <= lv and lv not in self.filled_buys:
                actions.append(("buy", lv))
            if p >= lv and lv not in self.filled_sells:
                actions.append(("sell", lv))
        for side, lv in actions:
            ord_res = self.place(side, lv)
            if side == "buy":
                self.filled_buys.add(lv)
            else:
                self.filled_sells.add(lv)
            self._save_state()
        return p, actions

def make_layout(symbol: str):
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
    )
    layout["body"].split_row(
        Layout(name="status"),
        Layout(name="logs"),
    )
    layout["header"].update(Panel(f"paradex_grid_bot {symbol}", box=box.ROUNDED))
    return layout

def render_status(p: float, actions):
    t = Table(box=box.SIMPLE_HEAVY)
    t.add_column("key")
    t.add_column("value")
    t.add_row("price", f"{p:.6f}")
    t.add_row("actions", str(len(actions)))
    if actions:
        for a in actions[:10]:
            t.add_row("action", f"{a[0]} @{a[1]}")
    return t

def tail_log(path: str, lines: int = 20):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read().splitlines()
            data = data[-lines:]
            return "\n".join(data)
    except Exception:
        return ""

def main():
    cfg = read_env()
    logger = setup_logging()
    exchange = setup_exchange(cfg["api_key"], cfg["api_secret"], cfg["network"])
    bot = GridBot(exchange, cfg["symbol"], cfg["lower"], cfg["upper"], cfg["lines"], cfg["qty"], cfg["dry_run"], logger)
    layout = make_layout(cfg["symbol"])
    with Live(layout, refresh_per_second=max(1, int(1/cfg["poll"]))):
        while True:
            try:
                p, actions = bot.step()
                layout["status"].update(render_status(p, actions))
                log_text = tail_log("logs/grid_bot.log", 40)
                layout["logs"].update(Panel(log_text or "", title="logs", box=box.ROUNDED))
                time.sleep(cfg["poll"])
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"LOOP_ERROR {e}")
                time.sleep(cfg["poll"])

if __name__ == "__main__":
    main()

