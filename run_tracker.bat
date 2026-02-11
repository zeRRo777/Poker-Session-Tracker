@echo off
TITLE Poker Session Tracker
ECHO Launching the application... Please wait.

CD /D "%~dp0"

IF NOT EXIST "venv" (
    ECHO Creating a virtual environment...
    python -m venv venv
    ECHO Installing libraries...
    call venv\Scripts\activate
    pip install -r requirements.txt
) ELSE (
    call venv\Scripts\activate
)

ECHO Open the browser...
streamlit run app.py --server.address localhost