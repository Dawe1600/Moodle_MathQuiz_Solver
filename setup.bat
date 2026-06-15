@echo off
echo ========================================================
echo Konfigurowanie srodowiska dla Moodle MathQuiz Solver...
echo ========================================================

echo.
echo Tworzenie wirtualnego srodowiska (venv)...
python -m venv venv

echo.
echo Aktywacja wirtualnego srodowiska i instalacja bibliotek...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo Instalowanie przegladarek dla biblioteki Playwright...
playwright install

echo.
echo ========================================================
echo Konfiguracja zakonczona sukcesem!
echo ========================================================
echo UWAGA: Przed uruchomieniem skryptu upewnij sie, ze:
echo 1. Skopiowales plik .env.example i nazwales go .env
echo 2. Wpisales swoj darmowy klucz GEMINI_API_KEY w pliku .env
echo.
echo Aby uruchomic bota, wpisz w konsoli:
echo call venv\Scripts\activate.bat
echo python bot.py
echo ========================================================
pause
