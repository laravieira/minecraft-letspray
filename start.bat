@ECHO OFF

:: Server Variables
SET window-title=LetsPray Vanilla
SET server-file=spigot-1.20.jar
SET server-memory=4G


:: Set Window Title
TITLE %window-title%

:: Open Minecraft Server
java -Xms%server-memory% -Xmx%server-memory% -jar %server-file% --nogui

:: End
PAUSE