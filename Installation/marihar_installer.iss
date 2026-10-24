; Marino RAKOTONJANAHARY - rakotonjanaharymarino@gmail.com
; ============================================================
;   MARIHAR - Script d'installation Complet (Version 1.0.0)
; ============================================================

#define MyAppName "MARIHAR"
#define MyAppVersion "1.0.0"
#define MyAppCopyright "Copyright 2026 MARIHAR"
#define MyAppDescription "Téléchargeur Vidéo Professionnel"
#define MyAppExeName "MARIHAR.exe"

[Setup]
AppId={{8F7B2D9A-4C3E-1A6F-9B8D-E2F4A7C9D1E5}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppCopyright={#MyAppCopyright}
AppPublisher={#MyAppName}
VersionInfoVersion={#MyAppVersion}
VersionInfoDescription={#MyAppDescription}
VersionInfoProductName={#MyAppName}

; Configuration des dossiers
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Sortie et visuel
LicenseFile=..\Docs\LICENSE.txt
OutputDir=installer_output
OutputBaseFilename=MARIHAR_Setup_v{#MyAppVersion}
SetupIconFile=..\Assets\Logo_marino.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardStyle=modern
Compression=lzma2/ultra
SolidCompression=yes
DisableWelcomePage=no

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Messages]
WelcomeLabel1=Bienvenue dans l'assistant d'installation de {#MyAppName}
WelcomeLabel2=Cet assistant va installer {#MyAppName} sur votre ordinateur.%n%nMARIHAR est une solution complète pour vos médias :%n• Téléchargement vidéo haute résolution (jusqu'en 4K)%n• Conversion et extraction audio haute fidélité%n• Support des playlists et sous-titres%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.%n%nCliquez sur Suivant pour commencer.

SelectDirLabel3=Veuillez choisir le dossier de destination pour l'installation.
ReadyLabel1=L'assistant est prêt à installer {#MyAppName}.%n%nCliquez sur Installer pour lancer le processus.

FinishedHeadingLabel=Installation terminée
FinishedLabel=L'installation de {#MyAppName} est maintenant terminée.%n%nL'application est prête à être utilisée. Merci d'avoir choisi MARIHAR !

[Tasks]
; L'icône de bureau est décochée par défaut
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Créer un raccourci dans la barre des tâches"; GroupDescription: "Raccourcis :"; Flags: unchecked
; LE PATH EST COCHÉ PAR DÉFAUT (Flag 'unchecked' supprimé)
Name: "addtopath"; Description: "Ajouter MARIHAR au PATH système (recommandé pour usage en ligne de commande)"; GroupDescription: "Options avancées :"

[Files]
; Exécutable principal
Source: "..\dist\MARIHAR\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Dossier _internal (Python et dépendances)
Source: "..\dist\MARIHAR\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; Dossier Binaries (yt-dlp, ffmpeg, ffprobe) - copié dans Binaries pour compatibilité
Source: "..\Binaries\*"; DestDir: "{app}\Binaries"; Flags: ignoreversion recursesubdirs createallsubdirs

; Fichiers de documentation
Source: "..\Docs\README_UTILISATEUR.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Docs\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Docs\Plateformes_supportées.txt"; DestDir: "{app}"; Flags: ignoreversion

; Assets (logo, etc.)
Source: "..\Assets\*"; DestDir: "{app}\Assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Quick Launch (optionnel)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer MARIHAR maintenant"; Flags: nowait postinstall skipifsilent unchecked
Filename: "{app}\README_UTILISATEUR.txt"; Description: "Afficher le guide d'utilisation"; Flags: postinstall skipifsilent unchecked shellexec

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// --- Message de bienvenue personnalisé ---
procedure InitializeWizard();
begin
  // Personnalisation si nécessaire
end;

// --- Vérification des prérequis ---
function InitializeSetup(): Boolean;
var
  Version: TWindowsVersion;
  Msg: string;
begin
  Result := True;
  
  // Obtenir la version de Windows
  GetWindowsVersionEx(Version);
  
  // Vérifier que c'est Windows 10 ou plus
  if (Version.Major < 10) then
  begin
    Msg := 'Ce logiciel nécessite Windows 10 ou Windows 11.'#13#10;
    Msg := Msg + 'Votre version de Windows n''est pas supportée.'#13#10#13#10;
    Msg := Msg + 'Voulez-vous continuer quand même ?';
    if MsgBox(Msg, mbError, MB_YESNO) = IDNO then
      Result := False;
  end;
  
  // Vérifier que c'est 64 bits
  if not Is64BitInstallMode then
  begin
    MsgBox('Ce logiciel nécessite une version 64 bits de Windows.', mbError, MB_OK);
    Result := False;
  end;
end;

// --- Gestion de l'ajout au PATH ---
procedure CurStepChanged(CurStep: TSetupStep);
var
  Path, AppPath: string;
begin
  if (CurStep = ssPostInstall) and IsTaskSelected('addtopath') then
  begin
    AppPath := ExpandConstant('{app}');
    if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', Path) then
    begin
      if Pos(';' + AppPath + ';', ';' + Path + ';') = 0 then
      begin
        RegWriteStringValue(HKEY_LOCAL_MACHINE, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', Path + ';' + AppPath);
      end;
    end;
  end;
end;

// --- Nettoyage à la désinstallation ---
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataPath: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataPath := ExpandConstant('{userappdata}\{#MyAppName}');
    if DirExists(DataPath) then
    begin
      if MsgBox('Voulez-vous supprimer vos paramètres personnels de {#MyAppName} ?', mbConfirmation, MB_YESNO) = IDYES then
      begin
        DelTree(DataPath, True, True, True);
      end;
    end;
  end;
end;