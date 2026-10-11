# Antibiotic Resistance Radar

Run the dashboard from this folder in PowerShell.

```powershell
# First-time setup (skip if .venv already exists)
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Start the dashboard (no activation required)
.\.venv\Scripts\python.exe -m streamlit run main.py
```

Use the virtual environment's Python to start Streamlit. Typing `streamlit`
directly may not work unless `.venv` is activated and its `Scripts` folder is
on `PATH`.

When Streamlit starts, open the **Local URL** it prints (normally http://localhost:8501).
In VS Code, open this project folder and select `.venv\Scripts\python.exe` with
**Python: Select Interpreter**. For the notebook, select the
**Python (.venv - Antibiotic Resistance)** kernel.

Upload a CSV in either long format (organism, antibiotic, result) or wide format (one row per isolate, one column per antibiotic). The sidebar lets you map the columns. Text results such as `R`/`Resistant` and `S`/`Susceptible` are recognized; numeric `0`/`1` values are treated as susceptible/resistant. Intermediate and unrecognized results are excluded from rates.