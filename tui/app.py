import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane

from tui.screens.dashboard import DashboardScreen
from tui.screens.runner    import RunnerScreen
from tui.screens.strategy  import StrategyScreen
from tui.screens.results   import ResultsScreen
from tui.screens.reports   import ReportsScreen


class JailbreakApp(App):
    CSS_PATH = "styles.tcss"
    TITLE    = "LLM Jailbreak Toolkit"
    SUB_TITLE = "AI Red-Team Research · Authorized use only"

    BINDINGS = [
        ("q", "quit",                    "Quit"),
        ("1", "switch_tab('dashboard')", "Dashboard"),
        ("2", "switch_tab('runner')",    "Runner"),
        ("3", "switch_tab('strategy')",  "Strategy"),
        ("4", "switch_tab('results')",   "Results"),
        ("5", "switch_tab('reports')",   "Reports"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="dashboard"):
            with TabPane("⚙  Dashboard", id="dashboard"):
                yield DashboardScreen()
            with TabPane("▶  Runner",    id="runner"):
                yield RunnerScreen()
            with TabPane("⛓  Strategy",  id="strategy"):
                yield StrategyScreen()
            with TabPane("📋  Results",  id="results"):
                yield ResultsScreen()
            with TabPane("📊  Reports",  id="reports"):
                yield ReportsScreen()
        yield Footer()

    def action_switch_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id
