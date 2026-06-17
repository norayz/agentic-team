"""Live terminal display using rich."""
import threading
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich import box
from datetime import datetime

_lock = threading.Lock()
_status = {
    "pm": "idle",
    "team_lead": "idle",
    "architect": "idle",
    "backend": "idle",
    "code_reviewer": "idle",
    "qa": "idle",
    "devops": "idle",
}
_log: list[str] = []


def update_agent_status(agent: str, status: str) -> None:
    with _lock:
        _status[agent] = status
        _log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {agent}: {status}")
        if len(_log) > 20:
            _log.pop(0)


def reset_agent(agent: str) -> None:
    with _lock:
        _status[agent] = "idle"


def get_display() -> dict:
    with _lock:
        return {"agents": dict(_status), "log": list(_log)}


def make_table() -> Table:
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold blue")
    agents = ["PM", "Team Lead", "Architect", "Backend", "CR", "QA", "DevOps"]
    keys = ["pm", "team_lead", "architect", "backend", "code_reviewer", "qa", "devops"]
    for agent in agents:
        table.add_column(agent, justify="center", min_width=14)
    with _lock:
        table.add_row(*[_status.get(k, "idle") for k in keys])
    return table


def start_display() -> None:
    """Start the blocking rich live display loop. Call from the orchestrator process."""
    console = Console()
    with Live(make_table(), refresh_per_second=2, console=console) as live:
        import time
        while True:
            live.update(
                Panel(
                    make_table(),
                    title="[bold blue]AGENTIC TEAM[/bold blue]",
                    subtitle="github.com/ylavi_tenb/agentic-team",
                )
            )
            time.sleep(0.5)
