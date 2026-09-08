"""UI utilities and ASCII art banners for Databricks Forge CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

FORGE_ASCII_ART = r"""
  ____        _        _          _      _          _____                     
 |  _ \  __ _| |_ __ _| |__  _ __(_) ___| | _____  |  ___|__  _ __ __ _  ___  
 | | | |/ _` | __/ _` | '_ \| '__| |/ __| |/ / __| | |_ / _ \| '__/ _` |/ _ \ 
 | |_| | (_| | || (_| | |_) | |  | | (__|   <\__ \ |  _| (_) | | | (_| |  __/ 
 |____/ \__,_|\__\__,_|_.__/|_|  |_|\___|_|\_\___/ |_|  \___/|_|  \__, |\___| 
                                                                  |___/       
        ███████╗ ██████╗ ██████╗  ██████╗ ███████╗     ██████╗██╗     ██╗
        ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝    ██╔════╝██║     ██║
        █████╗  ██║   ██║██████╔╝██║  ███╗█████╗      ██║     ██║     ██║
        ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝      ██║     ██║     ██║
        ██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗    ╚██████╗███████╗██║
        ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝     ╚═════╝╚══════╝╚═╝
"""


def render_forge_banner(console: Console, subtitle: str = "⚡ Industrial Lakehouse Engineering & CI/CD Toolkit") -> None:
    """Renders the stylized ASCII banner for Databricks Forge CLI."""
    banner_text = Text(FORGE_ASCII_ART, style="bold color(208)")
    
    panel = Panel(
        banner_text,
        title="[bold red]DATABRICKS FORGE CLI[/bold red]",
        subtitle=f"[bold cyan]{subtitle}[/bold cyan]",
        border_style="red",
        padding=(0, 1),
    )
    console.print(panel)
