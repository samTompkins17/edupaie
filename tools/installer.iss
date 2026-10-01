; ============================================================
; EduPaie — Script Inno Setup
; Génère l'installateur Windows : dist/EduPaie-Setup-<version>.exe
;
; Compilation :
;   tools\build_installer.bat
;   ou directement :
;   "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" tools\installer.iss
;
; Caractéristiques :
;   - installation par utilisateur (aucun droit administrateur requis)
;   - dossier : %LOCALAPPDATA%\Programs\EduPaie
;   - raccourcis : menu Démarrer + bureau (optionnel, décochable)
;   - désinstalleur avec entrée « Applications et fonctionnalités »
;   - les données (%APPDATA%\EduPaie) sont conservées à la désinstallation
; ============================================================

#define MyAppName "EduPaie"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "EduPaie"
#define MyAppExeName "EduPaie.exe"

[Setup]
AppId={{7E3F9C42-8D1A-4B6E-9C5F-2A4E8D7B1F30}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
; Laisser l'utilisateur choisir le lecteur/dossier (utile si C: est plein)
DisableDirPage=no
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Sortie dans output/ (dist/ est surveille par l'antivirus lors de la creation
; du fichier : output/ evite l'erreur EndUpdateResource)
OutputDir=..\output
OutputBaseFilename=EduPaie-Setup-{#MyAppVersion}
; Icône et bannière de l'installateur
SetupIconFile=..\resources\icon.ico
; Installation par utilisateur : aucun privilège requis
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Compression solide : reduce la taille du fichier final
SolidCompression=yes
Compression=lzma2/max
WizardStyle=modern
; Windows 10 minimum
MinVersion=10.0
; Pas de redémarrage automatique de l'application à la fin
; Le désinstalleur est placé dans {app} (suit le dossier choisi par
; l'utilisateur, important si le lecteur par défaut est saturé)
UninstallDisplayName={#MyAppName} {#MyAppVersion}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
; L'exécutable autonome construit par PyInstaller (build.bat)
Source: "..\dist\EduPaie.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Raccourci dans le menu Démarrer
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; Désinstalleur visible dans le menu Démarrer
Name: "{group}\Désinstaller {#MyAppName}"; Filename: "{uninstallexe}"
; Raccourci bureau (page optionnelle, décochable)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
; Case « Créer un raccourci sur le bureau » (cochée par défaut)
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
; Proposer de lancer EduPaie à la fin de l'installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Nettoie les fichiers générés par l'application dans son dossier d'installation
Type: filesandordirs; Name: "{app}\receipts"
