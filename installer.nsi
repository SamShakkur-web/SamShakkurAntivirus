; Script d'installation pour SamShakkur Antivirus
!include "MUI2.nsh"

; Paramètres de base
Name "SamShakkur Antivirus"
OutFile "SamShakkurAntivirus_Setup.exe"
InstallDir "$PROGRAMFILES\SamShakkurAntivirus"
InstallDirRegKey HKLM "Software\SamShakkurAntivirus" "Install_Dir"
RequestExecutionLevel admin

; Interface moderne
!define MUI_ICON "resources/icon.ico"
!define MUI_UNICON "resources/icon.ico"
!define MUI_ABORTWARNING

; Pages de l'installateur
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Pages de désinstallation
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Langues
!insertmacro MUI_LANGUAGE "French"

; Section d'installation
Section "Application"
  SectionIn RO
  
  ; Définir le répertoire d'installation
  SetOutPath $INSTDIR
  
  ; Copier les fichiers de l'application
  File "dist\SamShakkurAntivirus.exe"
  File /r "data"
  File /r "resources"
  File ".env"
  File "LICENSE.txt"
  File "README.md"
  
  ; Créer le raccourci dans le menu Démarrer
  CreateDirectory "$SMPROGRAMS\SamShakkurAntivirus"
  CreateShortCut "$SMPROGRAMS\SamShakkurAntivirus\SamShakkur Antivirus.lnk" "$INSTDIR\SamShakkurAntivirus.exe"
  CreateShortCut "$SMPROGRAMS\SamShakkurAntivirus\Désinstaller.lnk" "$INSTDIR\uninstall.exe"
  
  ; Créer le raccourci sur le bureau
  CreateShortCut "$DESKTOP\SamShakkur Antivirus.lnk" "$INSTDIR\SamShakkurAntivirus.exe"
  
  ; Écrire les informations d'installation
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SamShakkurAntivirus" "DisplayName" "SamShakkur Antivirus"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SamShakkurAntivirus" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SamShakkurAntivirus" "DisplayIcon" '"$INSTDIR\SamShakkurAntivirus.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SamShakkurAntivirus" "Publisher" "SamShakkur"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SamShakkurAntivirus" "DisplayVersion" "2.0.0"
  
  ; Créer le désinstallateur
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; Section de désinstallation
Section "Uninstall"
  ; Supprimer les fichiers
  RMDir /r "$INSTDIR"
  
  ; Supprimer les raccourcis
  Delete "$DESKTOP\SamShakkur Antivirus.lnk"
  RMDir /r "$SMPROGRAMS\SamShakkurAntivirus"
  
  ; Supprimer les clés de registre
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SamShakkurAntivirus"
  DeleteRegKey HKLM "Software\SamShakkurAntivirus"
SectionEnd
