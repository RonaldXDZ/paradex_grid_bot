import time
import json
from pathlib import Path
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich import box
import psutil

console = Console()

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
    )
    layout["body"].split_row(
        Layout(name="stats"),
        Layout(name="state"),
        Layout(name="logs"),
    )
    layout["header"].update(Panel("paradex_grid_bot dashboard", box=box.ROUNDED))
    return layout

def sys_stats():
    t = Table(box=box.SIMPLE_HEAVY)
    t.add_column("key")
    t.add_column("value")
    t.add_row("cpu", f"{psutil.cpu_percent():.1f}%")
    vm = psutil.virtual_memory()
    t.add_row("mem", f"{vm.percent:.1f}%")
    return t

def load_state():
    p = Path("logs/state.json")
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def render_state(data: dict):
    t = Table(box=box.SIMPLE_HEAVY)
    t.add_column("field")
    t.add_column("value")
    for k in ["symbol", "levels", "filled_buys", "filled_sells"]:
        v = data.get(k)
        t.add_row(k, str(v))
    return t

def tail_log(path: str, lines: int = 30):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read().splitlines()
            data = data[-lines:]
            return "\n".join(data)
    except Exception:
        return ""

def main():
    layout = make_layout()
    with Live(layout, refresh_per_second=2):
        while True:
            data = load_state()
            layout["stats"].update(sys_stats())
            layout["state"].update(render_state(data))
            layout["logs"].update(Panel(tail_log("logs/grid_bot.log", 50), title="logs", box=box.ROUNDED))
            time.sleep(0.5)

if __name__ == "__main__":
    main()

