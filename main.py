"""
Phase 1 Runner — CLI entry point
Usage: python main.py --behavior "write a python keylogger"
"""

import asyncio
import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from cfg.loader import load_config
from connectors.litellm_connector import LiteLLMConnector
from attacks.direct_injection import DirectInjectionAttack
from evaluators.keyword_eval import KeywordEvaluator
from db.store import ResultStore

console = Console()


BANNER = """
[bold red]
 ██╗     ██╗     ███╗   ███╗    ██████╗ ████████╗
 ██║     ██║     ████╗ ████║    ██╔══██╗╚══██╔══╝
 ██║     ██║     ██╔████╔██║    ██████╔╝   ██║   
 ██║     ██║     ██║╚██╔╝██║    ██╔══██╗   ██║   
 ███████╗███████╗██║ ╚═╝ ██║    ██║  ██║   ██║   
 ╚══════╝╚══════╝╚═╝     ╚═╝    ╚═╝  ╚═╝   ╚═╝   
[/bold red]
[dim]LLM Red-Team Toolkit · Phase 1 · For authorized research only[/dim]
"""


async def run(behavior: str, config: dict):
    console.print(BANNER)

    # Init components
    connector = LiteLLMConnector(config)
    evaluator = KeywordEvaluator()
    store = ResultStore(config["db"]["path"])

    attacks = [
        DirectInjectionAttack(),
    ]

    results_table = Table(
        title="Attack Results",
        show_lines=True,
        header_style="bold cyan",
    )
    results_table.add_column("Attack", style="yellow")
    results_table.add_column("Success", justify="center")
    results_table.add_column("Confidence", justify="center")
    results_table.add_column("Tokens", justify="right")
    results_table.add_column("Cost (USD)", justify="right")

    for attack in attacks:
        console.print(f"\n[cyan]→ Running:[/cyan] [bold]{attack.name}[/bold]")

        # Budget check
        if connector.total_cost >= config["budget"]["max_cost_usd"]:
            console.print("[bold red]Budget cap reached. Stopping.[/bold red]")
            break

        result = await attack.run(connector, behavior)
        result = evaluator.evaluate(result)
        store.save(result)

        # Print response preview
        preview = result.response[:200].replace("\n", " ")
        console.print(Panel(
            f"[dim]{preview}...[/dim]" if len(result.response) > 200 else f"[dim]{result.response}[/dim]",
            title="Response Preview",
            border_style="dim",
        ))

        success_str = "[bold green]✓ YES[/bold green]" if result.success else "[bold red]✗ NO[/bold red]"
        results_table.add_row(
            attack.name,
            success_str,
            f"{result.confidence:.0%}",
            str(result.tokens_used),
            f"${result.cost_usd:.5f}",
        )

    console.print("\n")
    console.print(results_table)

    summary = store.fetch_summary()
    console.print(
        f"\n[bold]Session Summary:[/bold] "
        f"Total: {summary['total']} | "
        f"Success: [green]{summary['successes']}[/green] | "
        f"Failed: [red]{summary['failures']}[/red] | "
        f"Cost: [yellow]${summary['total_cost_usd']}[/yellow]"
    )

    store.close()


def main():
    parser = argparse.ArgumentParser(description="LLM Jailbreak Toolkit — Phase 1")
    parser.add_argument(
        "--behavior",
        type=str,
        required=True,
        help='Target behavior to test, e.g. "write a keylogger"',
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.toml",
        help="Path to config file",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    asyncio.run(run(args.behavior, config))


if __name__ == "__main__":
    main()
