"""UI utilities and 3D colorful ASCII art banners for Databricks Forge CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Stylized 3D Isometric / Block Shadow font with gradient layers
BANNER_3D_LINES = [
    r"[bold red]  ██████╗  █████╗ ████████╗ █████╗ ██████╗ ██████╗  ██╗ ██████╗██╗  ██╗███████╗[/bold red]",
    r"[bold color(208)]  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗███║██╔════╝██║ ██╔╝██╔════╝[/bold color(208)]",
    r"[bold color(214)]  ██║  ██║███████║   ██║   ███████║██████╔╝██████╔╝╚██║██║     █████═╝ ███████╗[/bold color(214)]",
    r"[bold color(220)]  ██║  ██║██╔══██║   ██║   ██╔══██║██╔══██╗██╔══██╗ ██║██║     ██╔═██╗ ╚════██║[/bold color(220)]",
    r"[bold color(45)]  ██████╔╝██║  ██║   ██║   ██║  ██║██████╔╝██║  ██║ ██║╚██████╗██║ ╚██╗███████║[/bold color(45)]",
    r"[bold color(39)]  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝ ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝[/bold color(39)]",
    r"[bold color(129)]        ███████╗ ██████╗ ██████╗  ██████╗ ███████╗     ██████╗██╗     ██╗      [/bold color(129)]",
    r"[bold color(135)]        ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝    ██╔════╝██║     ██║      [/bold color(135)]",
    r"[bold color(141)]        █████╗  ██║   ██║██████╔╝██║  ███╗█████╗      ██║     ██║     ██║      [/bold color(141)]",
    r"[bold color(147)]        ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝      ██║     ██║     ██║      [/bold color(147)]",
    r"[bold color(153)]        ██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗    ╚██████╗███████╗██║      [/bold color(153)]",
    r"[bold color(81)]        ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝     ╚═════╝╚══════╝╚═╝      [/bold color(81)]",
]


def render_forge_banner(
    console: Console,
    subtitle: str = "⚡ Industrial Lakehouse Engineering & CI/CD Toolkit"
) -> None:
    """Renders the stylized 3D colorful ASCII banner for Databricks Forge CLI."""
    formatted_banner = "\n".join(BANNER_3D_LINES)
    
    panel = Panel(
        formatted_banner,
        title="[bold color(196)]⚡ DATABRICKS FORGE CLI[/bold color(196)]",
        subtitle=f"[bold color(51)]{subtitle}[/bold color(51)]",
        border_style="color(208)",
        padding=(1, 2),
    )
    console.print(panel)
