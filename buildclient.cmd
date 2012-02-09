:main
	@echo off
	:: buildclient.cmd - builds the cilent.zip file.
	::
	:: %1 is our desination folder for client.exe
	set destzip=%temp%\client%random%.7z
	set defdest=..\fishtankserver\download
	::
	:: check for 7-zip
	IF NOT EXIST "C:\program files\7-zip\." ECHO "NO 7-zip" & GOTO :eof
	:: check for %1
	IF x%1==x (
	 	ECHO No desination specified, using default Need to specify a destination %defdest%
		GOTO :eof
	) ELSE (
		SET exe=%1\\client.exe
	)
	
	IF EXIST %destzip% ERASE %destzip%
	IF EXIST %exe% ERASE %exe%
	
	set zip="C:\program files\7-zip\7z.exe"
	set sfx="c:\program files\7-zip\7zcon.sfx"
	
	ECHO Creating %exe% for distribution.
	
	CALL :copypython
	CALL :copyclient
	CALL :copysettings
::	CALL :copylibtorrent
	CALL :copyvc
	CALL :copymisc

	copy /b %sfx% + %destzip% %exe% > nul
	IF NOT EXIST %exe% ECHO ERROR copying %exe% & GOTO :eof
	dir %exe%
	
	erase %destzip%
    erase settings.example
	
	GOTO :eof

:copymisc
	:: copies folders we need to work
	ECHO misc directories...
	%zip% a %destzip% cloud\readme.txt > nul
	%zip% a %destzip% log\readme.txt > nul
	%zip% a %destzip% db\readme.txt > nul
	
	GOTO :eof

:copypython
	:: add Python
	ECHO python...
	%zip% a %destzip% misc\python*.msi > nul
	
	GOTO :eof

:copyclient
	:: Copy our client files to the lib directory
	ECHO   Main client\ files...
	%zip% a -r %destzip% client\* > nul
	ECHO   register.py
	%zip% a %destzip% register.py > nul
	ECHO   backuptest.py
	%zip% a %destzip% backuptest.py > nul
	ECHO   Cypto from misc.
	%zip% a -r %destzip% misc\Crypto > nul
	ECHO   runclient.cmd
	%zip% a %destzip% runclient.cmd > nul
	ECHO   installclient.cmd
	%zip% a %destzip% installclient.cmd > nul
	
	

	GOTO :eof

:copysettings
	ECHO Settings...
	::COPY settings.txt %destdir% > nul
    ECHO [settings] > settings.example
    ECHO .registerurl = /manager/register/ >> settings.example
    ECHO .settingurl = /manager/setting/ >> settings.example
    FOR /F "tokens=1" %%i in ('python buildclient.py') do echo .managerhost = %%i >> settings.example
	%zip% a %destzip% settings.example > nul

	GOTO :eof

:copylibtorrent
	ECHO Add libtorrent and necessary DLL's for it.
	PUSHD misc
	%zip% a %destzip% libtorrent\*  > nul
	POPD
	
	GOTO :eof

:copyvc
	ECHO VC++ distribution files
	%zip% a  %destzip% misc\vcredist_x86.exe > nul
	 
	GOTO :eof