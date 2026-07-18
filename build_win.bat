@echo off
REM Baut die Windows-App (dist\FKscript.exe).
REM Im Projektordner ausfuehren (Doppelklick oder in der Eingabeaufforderung).
cd /d "%~dp0"

if not exist .venv-win (
    python -m venv .venv-win
)

call .venv-win\Scripts\activate.bat
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt pyinstaller -q

pyinstaller --noconfirm --clean --windowed --onefile --name FKscript ^
    --add-data "Fahrtkostenerstattung_Familienheimfahrt.docx;." ^
    main.py

echo.
echo Fertig: dist\FKscript.exe
pause
