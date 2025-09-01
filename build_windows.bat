@echo off
echo [🔧] Construction de SamShakkur Antivirus pour Windows...
echo.

:: Vérifier que PyInstaller est installé
python -m pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo [❌] PyInstaller n'est pas installé
    echo [📦] Installation de PyInstaller...
    pip install pyinstaller
)

:: Nettoyer les builds précédents
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

:: Compiler avec tous les fichiers nécessaires
echo [🔨] Compilation en cours...
pyinstaller ^
  --name="SamShakkurAntivirus" ^
  --icon="resources/icon.ico" ^
  --add-data="src;src" ^
  --add-data="data;data" ^
  --add-data="resources;resources" ^
  --add-data=".env;." ^
  --hidden-import="streamlit" ^
  --hidden-import="flask" ^
  --hidden-import="stripe" ^
  --hidden-import="Crypto" ^
  --hidden-import="psutil" ^
  --hidden-import="pandas" ^
  --hidden-import="numpy" ^
  --hidden-import="requests" ^
  --hidden-import="python_dotenv" ^
  --hidden-import="cachetools" ^
  --hidden-import="sqlite3" ^
  --console ^
  --onefile ^
  --clean ^
  main.py

echo.
echo [✅] Compilation terminée !
echo [📁] L'application se trouve dans : dist\SamShakkurAntivirus.exe
echo.
pause
