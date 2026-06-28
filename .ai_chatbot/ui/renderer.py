import os
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.box import ROUNDED

console = Console()

class TerminalRenderer:
    @staticmethod
    def show_welcome_banner(backend_name: str, model_name: str, status_msg: str = ""):
        banner_text = Text()
        banner_text.append("⚡ Terminal AI Chatbot ⚡\n", style="bold cyan")
        banner_text.append("Your local-first, free, and lightweight chat companion.\n\n", style="italic dim")
        banner_text.append(f"Backend: ", style="bold")
        banner_text.append(f"{backend_name}\n", style="green")
        banner_text.append(f"Model: ", style="bold")
        banner_text.append(f"{model_name or 'Auto-select'}\n", style="green")
        if status_msg:
            banner_text.append(f"\n{status_msg}", style="yellow")
        
        banner_text.append("\nType ", style="dim")
        banner_text.append("/help", style="bold magenta")
        banner_text.append(" for slash commands or start chatting!", style="dim")

        panel = Panel(
            banner_text,
            title="[bold magenta]Welcome[/bold magenta]",
            border_style="magenta",
            box=ROUNDED,
            expand=False
        )
        console.print(panel)

    @staticmethod
    def show_help():
        table = Table(title="Slash Commands", box=ROUNDED, border_style="dim")
        table.add_column("Command", style="bold magenta", justify="left")
        table.add_column("Description", style="white", justify="left")
        
        table.add_row("/help", "Show this help menu")
        table.add_row("/model", "Switch backend or model")
        table.add_row("/system [prompt]", "Change or view the system persona")
        table.add_row("/clear", "Clear the terminal screen")
        table.add_row("/new", "Start a fresh conversation session")
        table.add_row("/save [name]", "Save current chat session")
        table.add_row("/load", "Select and load a saved chat session")
        table.add_row("/history", "View history metadata and saved sessions")
        table.add_row("/export [file]", "Export conversation to a markdown file")
        table.add_row("/tokens", "Estimate tokens in current session")
        table.add_row("/quit | /exit", "Exit the chatbot")

        console.print(table)

    @staticmethod
    def print_system_msg(msg: str):
        console.print(f"[bold yellow]ℹ {msg}[/bold yellow]")

    @staticmethod
    def print_error(msg: str):
        console.print(f"[bold red]❌ Error: {msg}[/bold red]")

    @staticmethod
    def print_success(msg: str):
        console.print(f"[bold green]✔ {msg}[/bold green]")

    @staticmethod
    def print_user_header():
        console.print("\n[bold cyan]👤 You[/bold cyan]")

    @staticmethod
    def print_assistant_header(backend: str, model: str):
        console.print(f"\n[bold magenta]🤖 AI ({backend} - {model})[/bold magenta]")

    @staticmethod
    def render_markdown(text: str):
        console.print(Markdown(text))

    @staticmethod
    def stream_response(stream_generator) -> str:
        """
        Render incoming stream chunks inside a live Rich interface.
        Returns the final full response string.
        """
        full_text = ""
        # Create a container text object that updates live
        with Live(Text("Thinking...", style="dim italic"), refresh_per_second=15, console=console) as live:
            first_chunk = True
            for chunk in stream_generator:
                if first_chunk:
                    # Clear the thinking spinner
                    live.update(Text(""))
                    first_chunk = False
                
                full_text += chunk
                # Re-render the markdown continuously
                live.update(Markdown(full_text))
        
        # Print final blank line for spacing
        console.print()
        return full_text
