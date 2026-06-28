import sys
import os
import datetime
from typing import Tuple, Optional
from ui.renderer import TerminalRenderer, console
from .chat_engine import ChatEngine

def handle_slash_command(command_line: str, engine: ChatEngine) -> Tuple[bool, Optional[str]]:
    """
    Handle slash commands.
    Returns a tuple (should_continue, status_message).
    - should_continue: True if chat session should continue, False if exit.
    - status_message: Optional message to print.
    """
    parts = command_line.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd in ("/quit", "/exit"):
        TerminalRenderer.print_system_msg("Goodbye!")
        return False, None

    elif cmd == "/help":
        TerminalRenderer.show_help()
        return True, None

    elif cmd == "/clear":
        os.system("cls" if os.name == "nt" else "clear")
        TerminalRenderer.show_welcome_banner(engine.active_backend_name, engine.active_model or "")
        return True, None

    elif cmd == "/new":
        engine.clear_history()
        engine.current_session_name = "default"
        TerminalRenderer.print_success("Started a new conversation session.")
        return True, None

    elif cmd == "/system":
        if not args:
            TerminalRenderer.print_system_msg(f"Current System Prompt:\n{engine.system_prompt}")
        else:
            engine.system_prompt = args
            TerminalRenderer.print_success(f"System prompt updated to:\n{args}")
        return True, None

    elif cmd == "/model":
        # Interactive model selector
        console.print("\n[bold cyan]Available Backends:[/bold cyan]")
        for i, name in enumerate(engine.backends.keys(), 1):
            avail = engine.backends[name].is_available()
            status = "[green]Available[/green]" if avail else "[red]Not Configured/Running[/red]"
            console.print(f" {i}. [bold]{name}[/bold] - {status}")

        try:
            choice = input("\nSelect backend number (or press Enter to cancel): ").strip()
            if not choice:
                return True, None
            
            backend_idx = int(choice) - 1
            backend_names = list(engine.backends.keys())
            if 0 <= backend_idx < len(backend_names):
                selected_backend = backend_names[backend_idx]
                
                # Retrieve models for selected backend
                models = engine.backends[selected_backend].get_available_models()
                if models:
                    console.print(f"\n[bold cyan]Available Models for {selected_backend}:[/bold cyan]")
                    for idx, model in enumerate(models, 1):
                        console.print(f" {idx}. {model}")
                    
                    model_choice = input("\nSelect model number (or press Enter for default): ").strip()
                    if model_choice:
                        model_idx = int(model_choice) - 1
                        if 0 <= model_idx < len(models):
                            engine.set_backend(selected_backend, models[model_idx])
                            TerminalRenderer.print_success(f"Switched to backend [bold]{selected_backend}[/bold] with model [bold]{models[model_idx]}[/bold]")
                        else:
                            TerminalRenderer.print_error("Invalid model selection.")
                    else:
                        engine.set_backend(selected_backend)
                        TerminalRenderer.print_success(f"Switched to backend [bold]{selected_backend}[/bold] with default model [bold]{engine.active_model}[/bold]")
                else:
                    engine.set_backend(selected_backend)
                    TerminalRenderer.print_success(f"Switched to backend [bold]{selected_backend}[/bold] (No models found; using fallback: {engine.active_model})")
            else:
                TerminalRenderer.print_error("Invalid backend selection.")
        except ValueError:
            TerminalRenderer.print_error("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            console.print()
            TerminalRenderer.print_system_msg("Model change cancelled.")
        return True, None

    elif cmd == "/save":
        session_name = args.strip() if args else input("Enter session name: ").strip()
        if not session_name:
            TerminalRenderer.print_error("Session name cannot be empty.")
            return True, None
        
        try:
            filepath = engine.save_session(session_name)
            TerminalRenderer.print_success(f"Session saved successfully to {filepath}")
        except Exception as e:
            TerminalRenderer.print_error(f"Failed to save session: {e}")
        return True, None

    elif cmd == "/load":
        sessions = engine.list_sessions()
        if not sessions:
            TerminalRenderer.print_system_msg("No saved sessions found.")
            return True, None

        console.print("\n[bold cyan]Saved Sessions:[/bold cyan]")
        for idx, s in enumerate(sessions, 1):
            console.print(f" {idx}. [bold]{s['name']}[/bold] ({s['backend']}/{s['model']}) - {s['messages_count']} messages - Last active: {s['updated_at']}")

        try:
            choice = input("\nSelect session number to load (or press Enter to cancel): ").strip()
            if not choice:
                return True, None
            
            session_idx = int(choice) - 1
            if 0 <= session_idx < len(sessions):
                selected = sessions[session_idx]["name"]
                if engine.load_session(selected):
                    TerminalRenderer.print_success(f"Loaded session [bold]{selected}[/bold] successfully.")
                else:
                    TerminalRenderer.print_error(f"Failed to load session {selected}.")
            else:
                TerminalRenderer.print_error("Invalid selection.")
        except ValueError:
            TerminalRenderer.print_error("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            console.print()
            TerminalRenderer.print_system_msg("Session load cancelled.")
        return True, None

    elif cmd == "/history":
        sessions = engine.list_sessions()
        TerminalRenderer.print_system_msg(f"Active Session: [bold]{engine.current_session_name}[/bold]")
        TerminalRenderer.print_system_msg(f"Total messages in active memory: {len(engine.history)}")
        if sessions:
            console.print("\n[bold cyan]All Sessions Saved on Disk:[/bold cyan]")
            for s in sessions:
                console.print(f" - [bold]{s['name']}[/bold] ({s['backend']}/{s['model']}) | {s['messages_count']} msgs | {s['updated_at']}")
        return True, None

    elif cmd == "/tokens":
        # Approximate tokens (words * 1.33)
        total_words = 0
        for m in engine.history:
            total_words += len(m["content"].split())
        total_words += len(engine.system_prompt.split())
        est_tokens = int(total_words * 1.33)
        
        TerminalRenderer.print_system_msg(f"Estimated current session tokens: ~{est_tokens}")
        TerminalRenderer.print_system_msg("Note: This is a rough word-count based estimate.")
        return True, None

    elif cmd == "/export":
        filename = args.strip() if args else input("Enter filename to export to (e.g. chat.md): ").strip()
        if not filename:
            TerminalRenderer.print_error("Filename cannot be empty.")
            return True, None

        if not filename.endswith(".md"):
            filename += ".md"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# Chat Session: {engine.current_session_name}\n")
                f.write(f"- **Backend**: {engine.active_backend_name}\n")
                f.write(f"- **Model**: {engine.active_model}\n")
                f.write(f"- **System Prompt**: {engine.system_prompt}\n")
                f.write(f"- **Exported At**: {datetime.datetime.now().isoformat()}\n\n")
                f.write("---\n\n")
                
                for msg in engine.history:
                    role_name = "User" if msg["role"] == "user" else "Assistant"
                    f.write(f"### 👤 {role_name}\n\n{msg['content']}\n\n")
            
            TerminalRenderer.print_success(f"Conversation exported successfully to {os.path.abspath(filename)}")
        except Exception as e:
            TerminalRenderer.print_error(f"Failed to export chat: {e}")
        return True, None

    else:
        TerminalRenderer.print_error(f"Unknown command: {cmd}. Type /help to see all available commands.")
        return True, None
