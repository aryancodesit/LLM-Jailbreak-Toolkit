from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input, Button, Label
from textual.containers import Container, Horizontal, VerticalScroll
from textual import on


class DashboardScreen(Widget):
    def compose(self) -> ComposeResult:
        with VerticalScroll():
            from cfg.loader import load_config
            config = load_config()

            yield Static("⚙  CONFIGURATION", classes="section-title")
            with Container(classes="panel"):
                yield Label("Target Model")
                yield Input(
                    value=config["target"]["model"],
                    id="model_input",
                    placeholder="e.g. groq/llama-3.1-8b-instant",
                )
                yield Label("API Key")
                yield Input(
                    value=config["target"]["api_key"],
                    id="api_key_input",
                    password=True,
                    placeholder="Your API key",
                )
                yield Label("Max Budget (USD)")
                yield Input(
                    value=str(config["budget"]["max_cost_usd"]),
                    id="budget_input",
                    placeholder="e.g. 1.0",
                )
                yield Button("💾  Save Config", id="save_btn", variant="error")

            yield Static("📊  SESSION STATS", classes="section-title")
            with Container(classes="panel", id="stats_panel"):
                yield Static("Loading...", id="stats_display")

            yield Static("📖  QUICK REFERENCE", classes="section-title")
            with Container(classes="panel"):
                yield Static(
                    "[dim]Free model strings:[/dim]\n"
                    "  [cyan]groq/llama-3.1-8b-instant[/cyan]       — Groq free tier (fastest)\n"
                    "  [cyan]groq/llama-3.3-70b-versatile[/cyan]    — Groq free tier (smarter)\n"
                    "  [cyan]gemini/gemini-1.5-flash[/cyan]          — Google free tier\n\n"
                    "[dim]Keybindings:[/dim]\n"
                    "  [cyan]1[/cyan] Dashboard   [cyan]2[/cyan] Runner   [cyan]3[/cyan] Strategy   [cyan]4[/cyan] Results   [cyan]5[/cyan] Reports   [cyan]q[/cyan] Quit",
                    markup=True,
                )

    def on_mount(self) -> None:
        self._refresh_stats()

    def _refresh_stats(self) -> None:
        from db.store import ResultStore
        from cfg.loader import load_config
        try:
            store = ResultStore(load_config()["db"]["path"])
            s = store.fetch_summary()
            store.close()
            self.query_one("#stats_display", Static).update(
                f"Total Runs : [white]{s['total']}[/white]\n"
                f"Successes  : [green]✓ {s['successes']}[/green]\n"
                f"Failures   : [red]✗ {s['failures']}[/red]\n"
                f"Total Cost : [yellow]${s['total_cost_usd']}[/yellow]"
            )
        except Exception as e:
            self.query_one("#stats_display", Static).update(f"[red]Error: {e}[/red]")

    @on(Button.Pressed, "#save_btn")
    def save_config(self) -> None:
        from cfg.loader import load_config
        config = load_config()
        config["target"]["model"] = self.query_one("#model_input", Input).value.strip()
        config["target"]["api_key"] = self.query_one("#api_key_input", Input).value.strip()
        try:
            config["budget"]["max_cost_usd"] = float(
                self.query_one("#budget_input", Input).value or "1.0"
            )
        except ValueError:
            self.notify("Invalid budget value!", severity="warning")
            return
        self._refresh_stats()
        self.notify("✓ Config saved for this session.", severity="information")
