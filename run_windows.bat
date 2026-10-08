@echo off
setlocal
pushd "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Chua cai moi truong Python. Hay lam theo buoc 4 trong README.md.
    pause
    popd
    exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 pause
popd
endlocal
