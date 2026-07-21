; Pomi Installer -- NSIS Script
Unicode true

!include "MUI2.nsh"

Name "Pomi"
OutFile "installer\Pomi_Setup_v1.0.0.exe"
InstallDir "$PROGRAMFILES64\Pomi"
RequestExecutionLevel admin

!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  ExecWait 'taskkill /f /im PomodoroTimer.exe' $0

  File "dist\Pomi.exe"
  File "README.md"

  CreateDirectory "$SMPROGRAMS\Pomi"
  CreateShortCut "$SMPROGRAMS\Pomi\Pomi.lnk" "$INSTDIR\Pomi.exe"
  CreateShortCut "$SMPROGRAMS\Pomi\Uninstall.lnk" "$INSTDIR\uninst.exe"
  CreateShortCut "$DESKTOP\Pomi.lnk" "$INSTDIR\Pomi.exe"

  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pomi" \
    "DisplayName" "Pomi"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pomi" \
    "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pomi" \
    "DisplayVersion" "1.0.0"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pomi" \
    "Publisher" "VirginiaH233"
SectionEnd

Section "Uninstall"
  ExecWait 'taskkill /f /im PomodoroTimer.exe' $0
  Delete "$INSTDIR\Pomi.exe"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\uninst.exe"
  RMDir "$INSTDIR"
  Delete "$SMPROGRAMS\Pomi\Pomi.lnk"
  Delete "$SMPROGRAMS\Pomi\Uninstall.lnk"
  RMDir "$SMPROGRAMS\Pomi"
  Delete "$DESKTOP\Pomi.lnk"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pomi"
SectionEnd
