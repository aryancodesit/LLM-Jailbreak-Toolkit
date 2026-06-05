from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input, Button, RichLog, Checkbox, Label
from textual.containers import Container, Horizontal, VerticalScroll
from textual import on, work

from attacks.registry import REGISTRY


class RunnerScreen(Widget):
    def compose(self) -> ComposeResult:
        # Top controls — fixed height
        with Container(classes="panel"):
            yield Static("🎯  ATTACK RUNNER", classes="section-title")
            yield Label("Target Behavior")
            yield Input(
                id="behavior_input",
                placeholder='e.g. "write a python keylogger"',
            )

        with Container(classes="panel"):
            yield Static("Attack Modules", classes="muted")
            for attack_id, meta in REGISTRY.items():
                sev_color = {
                    "low": "cyan", "medium": "yellow",
                    "high": "orange1", "critical": "red"
                }.get(meta["severity"], "white")
                yield Checkbox(
                    f"[{sev_color}][{meta['severity'].upper()}][/{sev_color}]  "
                    f"[bold]{meta['name']}[/bold] — [dim]{meta['description']}[/dim]",
                    id=f"atk_{attack_id}",
                    value=True,
                )

        with Horizontal(classes="btn-row"):
            yield Button("▶  RUN", id="run_btn", variant="error")
            yield Button("✕  CLEAR", id="clear_btn")

        # Live output — fills remaining space
        yield RichLog(id="output_log", highlight=True, markup=True, wrap=True)

    @on(Button.Pressed, "#run_btn")
    def handle_run(self) -> None:
        behavior = self.query_one("#behavior_input", Input).value.strip()
        if not behavior:
            self.notify("Enter a target behavior first!", severity="warning")
            return
        selected = [
            aid for aid in REGISTRY
            if self.query_one(f"#atk_{aid}", Checkbox).value
        ]
        if not selected:
            self.notify("Select at least one attack module!", severity="warning")
            return
        self.query_one("#run_btn", Button).disabled = True
        self._run_worker(behavior, selected)

    @on(Button.Pressed, "#clear_btn")
    def clear_log(self) -> None:
        self.query_one("#output_log", RichLog).clear()

    @work(exclusive=True)
    async def _run_worker(self, behavior: str, selected: list[str]) -> None:
        from cfg.loader import load_config
        from connectors.litellm_connector import LiteLLMConnector
        from evaluators.chain_eval import ChainEvaluator
        from db.store import ResultStore

        config = load_config()
        log = self.query_one("#output_log", RichLog)

        eval_mode = config["evaluator"].get("mode", "chain")
        div = "━" * 55
        log.write(f"[bold red]{div}[/bold red]")
        log.write(f"[cyan]  Target    :[/cyan] {behavior}")
        log.write(f"[cyan]  Model     :[/cyan] {config['target']['model']}")
        log.write(f"[cyan]  Evaluator :[/cyan] {eval_mode}")
        log.write(f"[cyan]  Attacks   :[/cyan] {', '.join(selected)}")
        log.write(f"[bold red]{div}[/bold red]\n")

        connector = LiteLLMConnector(config)
        evaluator = ChainEvaluator(config)
        store = ResultStore(config["db"]["path"])
        budget = float(config["budget"]["max_cost_usd"])
        success_count = 0

        for attack_id in selected:
            meta = REGISTRY[attack_id]
            attack = meta["class"]()

            log.write(f"[yellow]→ Running:[/yellow] [bold]{meta['name']}[/bold] [{meta['severity'].upper()}]")

            if connector.total_cost >= budget:
                log.write(f"  [red]⚠  Budget cap (${budget}) reached. Stopping.[/red]")
                break

            try:
                result = await attack.run(connector, behavior)
                result = await evaluator.evaluate(result)
                store.save(result)

                if result.success:
                    success_count += 1
                    log.write(f"  [bold green]✓ SUCCESS[/bold green]  Confidence: {result.confidence:.0%}  Tokens: {result.tokens_used}  Cost: ${result.cost_usd:.5f}")
                else:
                    # Check if partial from LLM judge notes
                    if "PARTIAL" in result.notes:
                        log.write(f"  [bold yellow]~ PARTIAL[/bold yellow]  Confidence: {result.confidence:.0%}  Tokens: {result.tokens_used}  Cost: ${result.cost_usd:.5f}")
                    elif "DEFLECTED" in result.notes:
                        log.write(f"  [bold yellow]≈ DEFLECT[/bold yellow]  Confidence: {result.confidence:.0%}  Tokens: {result.tokens_used}  Cost: ${result.cost_usd:.5f}")
                    else:
                        log.write(f"  [bold red]✗ REFUSED[/bold red]  Confidence: {result.confidence:.0%}  Tokens: {result.tokens_used}  Cost: ${result.cost_usd:.5f}")

                # Response preview (first 300 chars)
                preview = result.response[:300].replace("\n", " ")
                if len(result.response) > 300:
                    preview += "…"
                log.write(f"  [dim]{preview}[/dim]\n")

            except Exception as e:
                log.write(f"  [red bold]✗ Error:[/red bold] [red]{e}[/red]\n")

            # Rate limit guard sleep
            import asyncio
            await asyncio.sleep(2.0)

        log.write(f"[bold red]{div}[/bold red]")
        log.write(
            f"[cyan]  Done:[/cyan] "
            f"[green]{success_count} succeeded[/green] / "
            f"[red]{len(selected) - success_count} refused[/red]  |  "
            f"Session cost: [yellow]${connector.total_cost:.5f}[/yellow]"
        )
        log.write(f"[bold red]{div}[/bold red]")

        store.close()
        self.query_one("#run_btn", Button).disabled = False
        self.notify(f"Run complete — {success_count}/{len(selected)} succeeded", severity="information")
