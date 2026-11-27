@echo off
rem Runs the private question-worker a few times a day while the laptop is on.
rem Silently does nothing useful until OPENROUTER_API_KEY (or OMNIROUTE_API_KEY)
rem is set in the environment -- see pipeline/src/llm_gateway.py.
cd /d "D:\CODING\tesis"
echo ---- %date% %time% ---- >> "docs\thesis_audit\scheduled_worker.log"
".venv\Scripts\python.exe" -I -X utf8 "thesis\tools\question_worker.py" --max-items 2 >> "docs\thesis_audit\scheduled_worker.log" 2>&1
