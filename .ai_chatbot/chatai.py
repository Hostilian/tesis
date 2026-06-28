import os
import sys
# Inject parent directory into path so that config, engine, and ui modules are resolved locally
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style

from config import DEFAULT_CONFIG_DIR, ensure_config_dir
from engine.chat_engine import ChatEngine
from engine.commands import handle_slash_command
from ui.renderer import TerminalRenderer, console

# Setup custom style for prompt_toolkit
style = Style.from_dict({
    'prompt': 'bold cyan',
})

def check_and_setup_ollama(engine: ChatEngine):
    """
    Ensure Ollama is running and has a model pulled.
    If not, assist the user.
    """
    if engine.active_backend_name != "ollama":
        return

    backend = engine.active_backend
    if not backend.is_available():
        TerminalRenderer.print_system_msg(
            "Ollama does not seem to be running. Make sure the Ollama desktop app is open."
        )
        TerminalRenderer.print_system_msg(
            "Continuing... If you set Gemini/Groq keys, switch via: /model"
        )
        return

    models = backend.get_available_models()
    if not models:
        default_model = engine.config.get("default_model", "gemma3:4b")
        console.print(f"\n[bold yellow]No local models found in Ollama.[/bold yellow]")
        console.print(f"Would you like to pull [bold green]{default_model}[/bold green] now? (y/n)")
        
        try:
            choice = input("> ").strip().lower()
            if choice == "y":
                console.print(f"Pulling {default_model} from Ollama registry. This might take a few minutes...")
                # We can stream progress from pull_model
                last_status = ""
                for progress in backend.pull_model(default_model):
                    status = progress.get("status", "")
                    if status == "downloading":
                        completed = progress.get("completed", 0)
                        total = progress.get("total", 0)
                        if total > 0:
                            percent = (completed / total) * 100
                            mb_comp = completed / (1024 * 1024)
                            mb_total = total / (1024 * 1024)
                            status_msg = f"Downloading: {percent:.1f}% ({mb_comp:.1f}MB / {mb_total:.1f}MB)"
                        else:
                            status_msg = "Downloading..."
                    elif status == "error":
                        TerminalRenderer.print_error(progress.get("error", "Unknown pull error"))
                        break
                    else:
                        status_msg = status
                    
                    if status_msg != last_status:
                        print(f"\r{status_msg}", end="", flush=True)
                        last_status = status_msg
                print() # New line after completion
                
                # Verify pulling succeeded
                if backend.get_available_models():
                    TerminalRenderer.print_success(f"Successfully pulled {default_model}!")
                    engine.active_model = default_model
                else:
                    TerminalRenderer.print_error("Failed to pull model or model is not listed yet.")
            else:
                TerminalRenderer.print_system_msg("Skipped model pull. You must pull a model manually using: ollama pull <model>")
        except KeyboardInterrupt:
            print()
            TerminalRenderer.print_system_msg("Cancelled model setup.")

def main():
    parser = argparse.ArgumentParser(description="Terminal AI Chatbot")
    parser.add_argument("--backend", type=str, help="LLM backend to use (ollama, gemini, groq)")
    parser.add_argument("--model", type=str, help="Specific model name to use")
    args = parser.parse_args()

    ensure_config_dir()
    
    # Initialize Engine
    engine = ChatEngine()
    
    # Override settings from args if provided
    if args.backend:
        engine.set_backend(args.backend, args.model)
    elif args.model:
        engine.active_model = args.model

    # Check/Setup Ollama models
    check_and_setup_ollama(engine)

    # Initialize prompt history
    history_path = os.path.join(DEFAULT_CONFIG_DIR, "prompt_history.txt")
    session = PromptSession(
        history=FileHistory(history_path),
        auto_suggest=AutoSuggestFromHistory(),
        style=style
    )

    # Show Banner
    TerminalRenderer.show_welcome_banner(engine.active_backend_name, engine.active_model or "None")

    # Main Chat Loop
    while True:
        try:
            # Render input prompt
            prompt_str = f"\n({engine.current_session_name}) > "
            user_input = session.prompt(prompt_str).strip()
            
            if not user_input:
                continue

            # Handle slash commands
            if user_input.startswith("/"):
                should_continue, _ = handle_slash_command(user_input, engine)
                if not should_continue:
                    break
                continue

            # Add to local history
            engine.add_message("user", user_input)

            # Generate reply
            TerminalRenderer.print_assistant_header(engine.active_backend_name, engine.active_model or "auto")
            
            # Start streaming response from backend
            stream = engine.active_backend.generate_stream(
                messages=engine.get_messages_for_api(),
                system_prompt=engine.system_prompt,
                model=engine.active_model
            )
            
            # Render response
            response_text = TerminalRenderer.stream_response(stream)
            
            # Save assistant reply to history
            engine.add_message("assistant", response_text)
            
            # Auto-save session after each turn to avoid data loss
            engine.save_session()

        except KeyboardInterrupt:
            # Handle Ctrl+C (stop response generation or prompt refresh)
            console.print("\n[yellow]Interrupted.[/yellow]")
            continue
        except EOFError:
            # Handle Ctrl+D (exit)
            TerminalRenderer.print_system_msg("Exiting...")
            break
        except Exception as e:
            TerminalRenderer.print_error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
