@ECHO OFF

:: Server Variables
SET window-title=LetsPray
SET server-file=fabric-server-mc.1.19.2-loader.0.14.19-launcher.0.11.2.jar
SET server-memory=8G


:: Set Window Title
TITLE %window-title%

:: Open Minecraft Server
java -Xms%server-memory% -Xmx%server-memory% -jar %server-file% --nogui

:: End
PAUSE