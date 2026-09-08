"""UI utilities and 3D colorful ASCII art banners for Databricks Forge CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Stylized 3D Cyberpunk Isometric / Neon Block typography
BANNER_3D_LINES = [
    r"[bold color(201)]  ██████╗  █████╗ ████████╗ █████╗ ██████╗ ██████╗ ██╗ ██████╗██╗  ██╗[/bold color(201)]",
    r"[bold color(198)]  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██║██╔════╝██║ ██╔╝[/bold color(198)]",
    r"[bold color(207)]  ██║  ██║███████║   ██║   ███████║██████╔╝██████╔╝██║██║     █████═╝ [/bold color(207)]",
    r"[bold color(45)]  ██║  ██║██╔══██║   ██║   ██╔══██║██╔══██╗██╔══██╗██║██║     ██╔═██╗ [/bold color(45)]",
    r"[bold color(51)]  ██████╔╝██║  ██║   ██║   ██║  ██║██████╔╝██║  ██║██║╚██████╗██║ ╚██╗[/bold color(51)]",
    r"[bold color(87)]  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝[/bold color(87)]",
    r"[bold color(93)]  ░▒▓█[color(51)] CYBER-LAKEHOUSE [/color(51)]█▓▒░ [color(226)]// PROTOCOL 2077 //[/color(226)] ░▒▓█[color(201)] NEON-FORGE [/color(201)]█▓▒░[/bold color(93)]",
    r"[bold color(226)]      ███████╗ ██████╗ ██████╗  ██████╗ ███████╗    ██████╗██╗     ██╗ [/bold color(226)]",
    r"[bold color(220)]      ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝   ██╔════╝██║     ██║ [/bold color(220)]",
    r"[bold color(45)]      █████╗  ██║   ██║██████╔╝██║  ███╗█████╗     ██║     ██║     ██║ [/bold color(45)]",
    r"[bold color(51)]      ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝     ██║     ██║     ██║ [/bold color(51)]",
    r"[bold color(198)]      ██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗   ╚██████╗███████╗██║ [/bold color(198)]",
    r"[bold color(201)]      ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝    ╚═════╝╚══════╝╚═╝ [/bold color(201)]",
]


def render_forge_banner(
    console: Console,
    subtitle: str = "⚡ Neon Industrial Lakehouse Engineering & CI/CD Toolkit"
) -> None:
    """Renders the stylized 3D Cyberpunk ASCII banner for Databricks Forge CLI."""
    formatted_banner = "\n".join(BANNER_3D_LINES)
    
    panel = Panel(
        formatted_banner,
        title="[bold color(51)]◢◤ [bold color(201)]DATABRICKS FORGE CLI[/bold color(201)] [bold color(226)]// CYBERPUNK 3D //[/bold color(226)] ◢◤[/bold color(51)]",
        subtitle=f"[bold color(51)]{subtitle}[/bold color(51)]",
        border_style="color(201)",
        padding=(1, 1),
    )
    console.print(panel)
