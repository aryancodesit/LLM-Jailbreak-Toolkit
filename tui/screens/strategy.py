from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input, Button, RichLog, Label, Select
from textual.containers import Container, Horizontal
from textual import on, work

from engine.strategy import list_strategies, load_strategy


class StrategyScreen(Widget):
    def compose(self) -> ComposeResult:
        yield Static("⛓  STRATEGY ENGINE", classes="section-title")

        with Container(classes="panel"):
            yield Label("Target Behavior")
            yield Input(
                id="strategy_behavior_input",
                placeholder='e.g. "write a python keylogger"',
            )
            yield Label("Strategy")
            strategies = list_strategies()
            yield Select(
                [(s, s) for s in strategies],
                id="strategy_select",
                value=strategies[0] if strategies else Select.BLANK,
            )

        with Container(classes="panel", id="strategy_info"):
            yield Static("Select a strategy to see details.", id="strategy_desc")

        with Horizontal(classes="btn-row"):
            yield Button("⛓  RUN STRATEGY", id="strategy_run_btn", variant="error")
            yield Button("✕  CLEAR",         id="strategy_clear_btn")

        yield RichLog(id="strategy_log", highlight=True, markup=True, wrap=True)

    def on_mount(self) -> None:
        self._update_description()

    @on(Select.Changed, "#strategy_select")
    def on_strategy_changed(self, event: Select.Changed) -> None:
        self._update_description()

    def _update_description(self) -> None:
        try:
            sel = self.query_one("#strategy_select", Select).value
            if sel == Select.BLANK:
                return
            s = load_strategy(str(sel))
            steps = s.get("steps", [])
            step_lines = []
            for i, step in enumerate(steps, 1):
                if "combo" in step:
                    step_lines.append(f"  {i}. [magenta]COMBO[/magenta] {' + '.join(step['combo'])}")
                else:
                    step_lines.append(f"  {i}. {step['attack']}")
            stop = "[green]yes[/green]" if s.get("stop_on_success", True) else "[yellow]no (full scan)[/yellow]"
            desc = (
                f"[bold white]{s['name']}[/bold white]\n"
                f"[dim]{s.get('description', '')}[/dim]\n\n"
                f"Stop on success: {stop}\n"
                f"Steps ({len(steps)}):\n" + "\n".join(step_lines)
            )
            self.query_one("#strategy_desc", Static).update(desc)
        except Exception as e:
            self.query_one("#strategy_desc", Static).update(f"[red]{e}[/red]")

    @on(Button.Pressed, "#strategy_run_btn")
    def handle_run(self) -> None:
        behavior = self.query_one("#strategy_behavior_input", Input).value.strip()
        if not behavior:
            self.notify("Enter a target behavior first!", severity="warning")
            return
        sel = self.query_one("#strategy_select", Select).value
        if sel == Select.BLANK:
            self.notify("Select a strategy!", severity="warning")
            return
        self.query_one("#strategy_run_btn", Button).disabled = True
        self._run_worker(behavior, str(sel))

    @on(Button.Pressed, "#strategy_clear_btn")
    def clear_log(self) -> None:
        self.query_one("#strategy_log", RichLog).clear()

    @work(exclusive=True)
    async def _run_worker(self, behavior: str, strategy_name: str) -> None:
        from cfg.loader import load_config
        from connectors.litellm_connector import LiteLLMConnector
        from evaluators.chain_eval import ChainEvaluator
        from db.store import ResultStore
        from engine.chain_runner import ChainRunner
        from engine.strategy import load_strategy

        config   = load_config()
        log      = self.query_one("#strategy_log", RichLog)
        strategy = load_strategy(strategy_name)

        div = "━" * 55
        log.write(f"[bold red]{div}[/bold red]")
        log.write(f"[cyan]  Strategy :[/cyan] [bold]{strategy['name']}[/bold]")
        log.write(f"[cyan]  Target   :[/cyan] {behavior}")
        log.write(f"[cyan]  Model    :[/cyan] {config['target']['model']}")
        log.write(f"[bold red]{div}[/bold red]\n")

        connector = LiteLLMConnector(config)
        evaluator = ChainEvaluator(config)
        store     = ResultStore(config["db"]["path"])
        runner    = ChainRunner(connector, evaluator, store)

        async def on_step(step_result):
            """Live callback — fires after each step completes."""
            r      = step_result.attack_result
            action = step_result.action
            step_n = step_result.step_number

            sev_map = {
                "stop_success":     "[bold green]✓ SUCCESS → STOPPED[/bold green]",
                "continue_success": "[bold green]✓ SUCCESS → CONTINUING[/bold green]",
                "escalate":         "[bold red]✗ REFUSED → ESCALATING[/bold red]",
                "exhausted":        "[bold yellow]✗ REFUSED → EXHAUSTED[/bold yellow]",
            }
            label = sev_map.get(action, f"[white]{action}[/white]")

            log.write(
                f"  [yellow]Step {step_n}[/yellow] "
                f"[bold]{r.attack_name}[/bold]  {label}"
            )
            log.write(
                f"           Confidence: {r.confidence:.0%}  "
                f"Tokens: {r.tokens_used}  Cost: ${r.cost_usd:.5f}"
            )
            preview = r.response[:250].replace("\n", " ")
            if len(r.response) > 250:
                preview += "…"
            log.write(f"  [dim]{preview}[/dim]\n")

        chain = await runner.run(strategy, behavior, on_step=on_step)

        log.write(f"[bold red]{div}[/bold red]")
        if chain.final_success:
            log.write(
                f"  [bold green]⛓ CHAIN COMPLETE — SUCCESS[/bold green]\n"
                f"  Winning attack : [green]{chain.winning_attack}[/green]  "
                f"(Step {chain.winning_step})\n"
                f"  Steps run      : {len(chain.steps)}\n"
                f"  Total tokens   : {chain.total_tokens}\n"
                f"  Total cost     : [yellow]${chain.total_cost_usd:.5f}[/yellow]"
            )
        else:
            log.write(
                f"  [bold red]⛓ CHAIN EXHAUSTED — ALL ATTACKS REFUSED[/bold red]\n"
                f"  Steps run  : {len(chain.steps)}\n"
                f"  Total cost : [yellow]${chain.total_cost_usd:.5f}[/yellow]"
            )
        log.write(f"[bold red]{div}[/bold red]")

        store.close()
        self.query_one("#strategy_run_btn", Button).disabled = False
        status = "SUCCESS" if chain.final_success else "EXHAUSTED"
        self.notify(f"Strategy complete — {status}", severity="information")
