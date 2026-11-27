@echo off
rem Runs the private question worker a few times a day while the laptop is on
rem (Windows Task Scheduler entry "ThesisBacklogWorker").
rem Provider "auto": your own OpenRouter key if set, else a local OmniRoute if it
rem answers, else your own Claude CLI (cheap "haiku" model, all tools disabled).
rem It writes private notes to docs\thesis_audit\worker_notes and never edits,
rem commits or sends anything.
cd /d "D:\CODING\tesis"
echo ---- %date% %time% ---- >> "docs\thesis_audit\scheduled_worker.log"
".venv\Scripts\python.exe" -I -X utf8 "thesis\tools\question_worker.py" --provider auto --max-items 3 --skip-done-today >> "docs\thesis_audit\scheduled_worker.log" 2>&1
