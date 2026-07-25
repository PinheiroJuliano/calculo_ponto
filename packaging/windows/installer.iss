#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#define AppName "Calculadora de Saida"
#define AppExeName "calculo-ponto.exe"
#define AppPublisher "PisJuliano e contribuidores"

[Setup]
AppId={{60AE5BFC-A39B-4659-8F85-9E67C17BC900}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://github.com/lucasfhs/calculo_ponto
AppSupportURL=https://github.com/lucasfhs/calculo_ponto/issues
AppUpdatesURL=https://github.com/lucasfhs/calculo_ponto/releases
VersionInfoCompany={#AppPublisher}
VersionInfoCopyright=Copyright (c) PisJuliano e contribuidores
VersionInfoDescription=Instalador da Calculadora de Saida
VersionInfoProductName={#AppName}
DefaultDirName={localappdata}\Programs\Calculo Ponto
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\release
OutputBaseFilename=calculo-ponto_{#AppVersion}_windows_x86_64_setup
SetupIconFile=..\..\assets\clock.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na area de trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Files]
Source: "..\..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\AUTHORS.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "CalculoPonto"; ValueType: none; Flags: uninsdeletevalue dontcreatekey

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Executar {#AppName}"; Flags: nowait postinstall skipifsilent
