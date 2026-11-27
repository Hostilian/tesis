@AGENTS.md

## Claude-specific notes

- For anything a person will read, load the `thesis-plain-english` skill (`.claude/skills/thesis-plain-english/SKILL.md`).
- `.venv` uses Python 3.12.5. `black` refuses to run on that version, so format with black 24.10.0 under another Python (CI runs `black --check pipeline/src/ pipeline/run_pipeline.py`).
- `pytest` may hit a locked temp folder on this machine. Use `--basetemp` with a folder under `%TEMP%`.
- Windows writes CRLF by default. Write any file whose bytes are hashed with explicit `\n` endings.
