@echo off
:: buildclient.cmd - builds the cilent.zip file.
::
:: %1 is our desination folder for client.exe
set destzip=%temp%\client%random%.7z
set defdest=C:\torrentserver\mserver\
:: check for 7-zip
IF NOT EXIST "C:\program files\7-zip\." ECHO "NO 7-zip" & GOTO :eof
:: check for %1
IF x%1==x (
 	ECHO No desination specified, using default Need to specify a destination %defdest%
 	SET exe=%defdest%client.exe
) ELSE (
	SET exe=%1\\client.exe
)
echo %exe%

set zip="C:\program files\7-zip\7z.exe"
set sfx="c:\program files\7-zip\7zcon.sfx"

:: add Python
ECHO Adding python...
cd misc
:: still in misc.
::XCOPY misc\python %destdir%\python /e/f/i > nul
%zip% a -r %destzip% python > nul
cd..

:: Copy our client files to the lib directory
ECHO Adding client files...
::XCOPY client\*.py %destdir%\client /e/f/i > nul
%zip% a -r %destzip% *.py > nul

ECHO Settings...
::COPY settings.txt %destdir% > nul
%zip% a %destzip% settings.txt > nul

ECHO Add libtorrent and necessary DLL's for it.
cd misc
::COPY misc\libtorrent\* %destdir%\python\lib\site-packages > nul
%zip% a %destzip% libtorrent\* > nul

ECHO Copy over VC++ distribution files to root for now.
::COPY misc\vcredist_x86.exe %destdir% > nul
%zip% a  %destzip% vcredist_x86.exe > nul
cd..

ECHO READY TO create %exe% and erase .zip
PAUSE
copy /b %sfx% + %destzip% %exe%
erase %destzip%
