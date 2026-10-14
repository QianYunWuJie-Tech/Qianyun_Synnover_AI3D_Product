Unicode true
!include "MUI2.nsh"
!include "x64.nsh"
!define PRODUCT "SYNNOVER AI3D Camera"
!ifndef PRODUCT_VERSION
!error "PRODUCT_VERSION must be supplied from deploy/release.json"
!endif
!ifndef PRODUCT_PAYLOAD
!define PRODUCT_PAYLOAD "../../dist/windows-viewer-rc2"
!endif
!ifndef PRODUCT_PAYLOAD_GLOB
!define PRODUCT_PAYLOAD_GLOB "${PRODUCT_PAYLOAD}/*"
!endif
!ifndef PRODUCT_INSTALLER
!define PRODUCT_INSTALLER "../../dist/SYNNOVER-AI3D-${PRODUCT_VERSION}-windows-x64-Setup.exe"
!endif
!ifndef PRODUCT_UNINSTALL_LIST
!define PRODUCT_UNINSTALL_LIST "payload-uninstall.nsh"
!endif
!define MUI_ICON "synnover-camera.ico"
!define MUI_UNICON "synnover-camera.ico"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\SYNNOVER-AI3D"
!include "FileFunc.nsh"
Var PreviousDir
Var PreviousRegView
Var PreviousUninstall
Var RestoreFirewall

; Opening with exclusive write access detects a running image without deleting
; anything. A cancelled/failed upgrade must leave the old installation intact.
!macro RequireViewerClosed DIRECTORY TAG
  ${TAG}_retry:
  ${If} ${FileExists} "${DIRECTORY}\bin\cleardepth-viewer.exe"
    System::Call 'kernel32::CreateFileW(w "${DIRECTORY}\bin\cleardepth-viewer.exe", i 0xC0000000, i 0, p 0, i 3, i 0, p 0) p.r0'
    ${If} $0 == -1
      MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "无法更新正在使用或无法写入的 Viewer。请关闭 SYNNOVER AI3D Camera 后重试；若仍失败，请检查安装目录权限。" /SD IDCANCEL IDRETRY ${TAG}_retry
      SetErrorLevel 1
      Abort
    ${EndIf}
    System::Call 'kernel32::CloseHandle(p r0)'
  ${EndIf}
!macroend
Name "${PRODUCT}"
OutFile "${PRODUCT_INSTALLER}"
InstallDir "$PROGRAMFILES64\SYNNOVER AI3D"
InstallDirRegKey HKLM "${UNINSTALL_KEY}" "InstallLocation"
RequestExecutionLevel admin
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"
Function .onInit
  SetRegView 64
  ${IfNot} ${RunningX64}
    MessageBox MB_OK "需要 Windows x64 系统"
    Abort
  ${EndIf}
  StrCpy $PreviousRegView 64
  ReadRegStr $PreviousDir HKLM "${UNINSTALL_KEY}" "InstallLocation"
  ReadRegStr $PreviousUninstall HKLM "${UNINSTALL_KEY}" "UninstallString"
  ${If} $PreviousDir == ""
    SetRegView 32
    StrCpy $PreviousRegView 32
    ReadRegStr $PreviousDir HKLM "${UNINSTALL_KEY}" "InstallLocation"
    ReadRegStr $PreviousUninstall HKLM "${UNINSTALL_KEY}" "UninstallString"
    SetRegView 64
  ${EndIf}
  ; Early releases had no uninstall registration. Recognize the known default
  ; directory, and also check the chosen destination when installation begins.
  ${If} $PreviousDir == ""
  ${AndIf} ${FileExists} "$PROGRAMFILES64\SYNNOVER AI3D\bin\cleardepth-viewer.exe"
    StrCpy $PreviousDir "$PROGRAMFILES64\SYNNOVER AI3D"
  ${EndIf}
  ${If} $PreviousDir != ""
  ${AndIf} $INSTDIR == "$PROGRAMFILES64\SYNNOVER AI3D"
    StrCpy $INSTDIR $PreviousDir
  ${EndIf}
FunctionEnd
Function RemovePreviousInstallation
  !insertmacro RequireViewerClosed "$INSTDIR" destination
  ${If} $PreviousDir == ""
  ${AndIf} ${FileExists} "$INSTDIR\bin\cleardepth-viewer.exe"
    StrCpy $PreviousDir $INSTDIR
  ${EndIf}
  ${If} $PreviousDir == ""
    Return
  ${EndIf}
  !insertmacro RequireViewerClosed "$PreviousDir" previous
  StrCpy $RestoreFirewall 0
  ClearErrors
  ExecWait `powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -Command "if (Get-NetFirewallRule -Name 'SYNNOVER-AI3D-Discovery' -ErrorAction SilentlyContinue | Where-Object Enabled -eq 'True') {exit 0} else {exit 2}"` $0
  ${IfNot} ${Errors}
  ${AndIf} $0 == 0
    StrCpy $RestoreFirewall 1
  ${EndIf}
  ${If} ${FileExists} "$PreviousDir\Uninstall.exe"
    DetailPrint "正在卸载旧版 SYNNOVER AI3D Camera…"
    InitPluginsDir
    ClearErrors
    CopyFiles /SILENT "$PreviousDir\Uninstall.exe" "$PLUGINSDIR\previous-uninstall.exe"
    ${If} ${Errors}
      Goto previous_failed
    ${EndIf}
    ; _?= is last and intentionally unquoted: NSIS consumes the full remaining
    ; path, including spaces, and does not launch a detached child uninstaller.
    ClearErrors
    ExecWait '"$PLUGINSDIR\previous-uninstall.exe" /S _?=$PreviousDir' $0
    ${If} ${Errors}
      Goto previous_failed
    ${EndIf}
    ${If} $0 != 0
      Goto previous_failed
    ${EndIf}
    ${If} ${FileExists} "$PreviousDir\bin\cleardepth-viewer.exe"
      Goto previous_failed
    ${EndIf}
  ${Else}
    ${If} $PreviousUninstall != ""
      Goto previous_failed
    ${EndIf}
    DetailPrint "正在迁移没有卸载程序的早期版本…"
    ; Only known product files: never recursively delete a customer's folder.
    StrCpy $1 $INSTDIR
    StrCpy $INSTDIR $PreviousDir
    !include "${PRODUCT_UNINSTALL_LIST}"
    Delete "$INSTDIR\启动 AI3D 相机.bat"
    StrCpy $INSTDIR $1
    ${If} ${FileExists} "$PreviousDir\bin\cleardepth-viewer.exe"
      Goto previous_failed
    ${EndIf}
  ${EndIf}
  ${If} $PreviousRegView == 32
    SetRegView 32
    DeleteRegKey HKLM "${UNINSTALL_KEY}"
    SetRegView 64
  ${EndIf}
  Return
  previous_failed:
  MessageBox MB_OK|MB_ICONSTOP "旧版本未能完成卸载，已停止安装新版。请关闭 Viewer 后重试；若旧卸载程序缺失，请先修复旧安装。保存的图像和点云不会被清理。" /SD IDOK
  SetErrorLevel 1
  Abort
FunctionEnd
Section "Viewer"
  SetRegView 64
  Call RemovePreviousInstallation
  SetOutPath "$INSTDIR"
  File /r "${PRODUCT_PAYLOAD_GLOB}"
  ; Remove the previous per-user shortcut and use one consistent all-users scope.
  SetShellVarContext current
  Delete "$SMPROGRAMS\SYNNOVER AI3D\AI3D 相机.lnk"
  RMDir "$SMPROGRAMS\SYNNOVER AI3D"
  SetShellVarContext all
  Delete "$SMPROGRAMS\SYNNOVER AI3D\AI3D 相机.lnk"
  RMDir "$SMPROGRAMS\SYNNOVER AI3D"
  Delete "$INSTDIR\启动 AI3D 相机.bat"
  CreateDirectory "$SMPROGRAMS\${PRODUCT}"
  CreateShortcut "$SMPROGRAMS\${PRODUCT}\${PRODUCT}.lnk" "$INSTDIR\bin\cleardepth-viewer.exe"
  CreateShortcut "$DESKTOP\${PRODUCT}.lnk" "$INSTDIR\bin\cleardepth-viewer.exe"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateShortcut "$SMPROGRAMS\${PRODUCT}\Uninstall ${PRODUCT}.lnk" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayName" "${PRODUCT}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegDWORD HKLM "${UNINSTALL_KEY}" "InstallerRevision" 2
  WriteRegStr HKLM "${UNINSTALL_KEY}" "Publisher" "SYNNOVER"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayIcon" '"$INSTDIR\bin\cleardepth-viewer.exe",0'
  WriteRegStr HKLM "${UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKLM "${UNINSTALL_KEY}" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
  WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  WriteRegDWORD HKLM "${UNINSTALL_KEY}" "EstimatedSize" $0
  ${If} $RestoreFirewall != 1
    MessageBox MB_YESNO|MB_DEFBUTTON2 "是否允许本应用在专用局域网发现相机？此操作不会关闭防火墙。" /SD IDNO IDNO skip_firewall
  ${EndIf}
  ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\firewall.ps1"'
  skip_firewall:
SectionEnd
Section "Uninstall"
  SetRegView 64
  ; Do not remove registration or other files while the application is still open.
  !insertmacro RequireViewerClosed "$INSTDIR" uninstall
  IfFileExists "$INSTDIR\bin\cleardepth-viewer.exe" 0 viewer_closed
  ClearErrors
  Delete "$INSTDIR\bin\cleardepth-viewer.exe"
  IfErrors 0 viewer_closed
  MessageBox MB_OK "请先关闭 SYNNOVER AI3D Camera，再运行卸载程序。" /SD IDOK
  SetErrorLevel 1
  Abort
  viewer_closed:
  ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\firewall.ps1" -Remove'
  DeleteRegKey HKLM "${UNINSTALL_KEY}"
  SetShellVarContext current
  Delete "$SMPROGRAMS\SYNNOVER AI3D\AI3D 相机.lnk"
  RMDir "$SMPROGRAMS\SYNNOVER AI3D"
  SetShellVarContext all
  Delete "$DESKTOP\${PRODUCT}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT}\${PRODUCT}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT}\Uninstall ${PRODUCT}.lnk"
  RMDir "$SMPROGRAMS\${PRODUCT}"
  ; Generated from the payload. Never recursively delete customer files.
  !include "${PRODUCT_UNINSTALL_LIST}"
  Delete "$INSTDIR\启动 AI3D 相机.bat"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
SectionEnd
