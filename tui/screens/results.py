from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, DataTable, Button, RichLog
from textual.containers import Horizontal, Container, Vertical
from textual import on


class ResultsScreen(Widget):
    def compose(self) -> ComposeResult:
        yield Static("📋  RESULTS HISTORY", classes="section-title")

        with Horizontal(classes="btn-row"):
            yield Button("↻  Refresh",    id="refresh_btn")
            yield Button("⬇  Export JSON", id="export_btn")
            yield Button("🗑  Clear DB",   id="clear_btn", variant="warning")

        # Top half — table
        with Container(classes="panel", id="table_panel"):
            yield DataTable(id="results_table", cursor_type="row")

        # Bottom half — detail view
        yield Static("  Row Detail", classes="muted")
        yield RichLog(id="detail_log", highlight=True, markup=True, wrap=True)

    def on_mount(self) -> None:
        table = self.query_one("#results_table", DataTable)
        table.add_columns(
            "ID", "Time", "Attack", "Target",
            "Result", "Conf", "Tokens", "Cost"
        )
        self._load()

    def _load(self) -> None:
        from db.store import ResultStore
        from cfg.loader import load_config
        store = ResultStore(load_config()["db"]["path"])
        rows = store.fetch_all()
        store.close()

        table = self.query_one("#results_table", DataTable)
        table.clear()
        self._rows = rows     # store for detail view

        for r in rows:
            result_str = "✓ YES" if r["success"] else "✗ NO"
            target = r["target"][:32] + "…" if len(r["target"]) > 32 else r["target"]
            table.add_row(
                str(r["id"]),
                r["timestamp"][5:19],    # strip year
                r["attack_name"],
                target,
                result_str,
                f"{r['confidence']:.0%}",
                str(r["tokens"]),
                f"${r['cost_usd']:.5f}",
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Show full detail of selected row in the detail panel."""
        log = self.query_one("#detail_log", RichLog)
        log.clear()
        try:
            row_index = event.cursor_row
            r = self._rows[row_index]
            log.write(f"[cyan]Attack   :[/cyan] {r['attack_name']}")
            log.write(f"[cyan]Target   :[/cyan] {r['target']}")
            log.write(f"[cyan]Time     :[/cyan] {r['timestamp']}")
            log.write(f"[cyan]Tokens   :[/cyan] {r['tokens']}  Cost: ${r['cost_usd']:.5f}")
            status = "[green]✓ SUCCESS[/green]" if r["success"] else "[red]✗ REFUSED[/red]"
            log.write(f"[cyan]Result   :[/cyan] {status}  Confidence: {r['confidence']:.0%}")
            log.write(f"\n[yellow]── PROMPT ──[/yellow]")
            log.write(f"[dim]{r['prompt']}[/dim]")
            log.write(f"\n[yellow]── RESPONSE ──[/yellow]")
            log.write(f"[dim]{r['response']}[/dim]")
            if r.get("notes"):
                log.write(f"\n[yellow]── NOTES ──[/yellow]")
                log.write(f"[dim]{r['notes']}[/dim]")
        except Exception as e:
            log.write(f"[red]Error loading detail: {e}[/red]")

    @on(Button.Pressed, "#refresh_btn")
    def refresh_results(self) -> None:
        self._load()
        self.notify("↻ Results refreshed!")

    @on(Button.Pressed, "#export_btn")
    def export(self) -> None:
        import json
        from db.store import ResultStore
        from cfg.loader import load_config
        store = ResultStore(load_config()["db"]["path"])
        rows = store.fetch_all()
        store.close()
        with open("results_export.json", "w") as f:
            json.dump(rows, f, indent=2)
        self.notify("✓ Exported to results_export.json!", severity="information")

    @on(Button.Pressed, "#clear_btn")
    def clear_db(self) -> None:
        import sqlite3
        from cfg.loader import load_config
        path = load_config()["db"]["path"]
        conn = sqlite3.connect(path)
        conn.execute("DELETE FROM results")
        conn.commit()
        conn.close()
        self._load()
        self.query_one("#detail_log", RichLog).clear()
        self.notify("🗑  Database cleared.", severity="warning")
