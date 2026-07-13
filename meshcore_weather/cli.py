"""
Command line interface for MeshCore Weather Gateway.
"""

from rich.console import Console

from meshcore_weather.version import __version__

console = Console()


def main() -> None:
    """
    Main CLI entry point.
    """

    console.print()

    console.print(
        "[bold cyan]MeshCore Weather Gateway[/bold cyan]"
    )

    console.print(
        f"Version: [green]{__version__}[/green]"
    )

    console.print()

    console.print(
        "Application successfully started."
    )
