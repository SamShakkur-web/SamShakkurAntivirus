@echo off
echo [🏗️] Construction complète de SamShakkur Antivirus...
echo.

:: Étape 1: Compiler l'application
call build_windows.bat

:: Étape 2: Créer l'installateur
if exist "SamShakkurAntivirus_Setup.exe" del "SamShakkurAntivirus_Setup.exe"

echo [📦] Création de l'installateur...
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    "C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
) else if exist "C:\Program Files\NSIS\makensis.exe" (
    "C:\Program Files\NSIS\makensis.exe" installer.nsi
) else (
    echo [❌] NSIS non trouvé. Installation de NSIS requis.
    echo [🌐] Téléchargez NSIS depuis: https://nsis.sourceforge.io/Download
    pause
    exit 1
)

if exist "SamShakkurAntivirus_Setup.exe" (
    echo [✅] Installateur créé: SamShakkurAntivirus_Setup.exe
    echo.
    echo [🎉] Construction terminée avec succès!
    echo [📦] Fichier d'installation: SamShakkurAntivirus_Setup.exe
    echo [💾] Taille: %~z0 bytes
) else (
    echo [❌] Erreur lors de la création de l'installateur
)

echo.
pause
