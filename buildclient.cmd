@echo off
:main
    :: 
    :: buildclient.cmd - builds the distributable version of client.  This only works from a
    :: working client setup.
    
    ::
    :: check for things, call the buildenv.cmd to setup local environment.
    ::
    
    ECHO Environment check ...
    :: settings.txt
    IF NOT EXIST settings.txt CALL :error "settings.txt not found, create and try again" & GOTO :eof
    :: buildclient.py
    IF NOT EXIST buildclient.py CALL :error "buildclient.py not found" & GOTO :eof
    :: buildenv.cmd
    IF NOT EXIST buildenv.cmd CALL :error "buildenv.cmd not found, need to create to run" & GOTO :eof
    CALL buildenv.cmd
    
    :: agentservice.spec
    IF NOT EXIST agentservice.spec CALL :error "agentservice.spec not found" & GOTO :eof
    
    :: 7zip and SFX necessary.
    IF NOT EXIST %zip% CALL :error "%zip% not found" & GOTO :eof
    IF NOT EXIST %sfx% CALL :error "%sfx% not found" & GOTO :eof
    
    ECHO Build EXE's ...    
    :: call pyinstaller
    python %pyinst%\build.py --noconfirm agentservice.spec > nul
    IF NOT %errorlevel%==0 CALL :error "Error %errorlevel% on building" & GOTO :eof

    ECHO Building settings.txt ...
    :: at this point, the dist directory should have what we want.
    :: so build a settings.txt and then zip it all up.
    python buildclient.py dist\agent\ > nul
    IF NOT %errorlevel%==0 CALL :error "Error calling buildclient.py" & GOTO :eof
    
    ECHO Create .EXE zip file for distribution, and copy ...
    :: everything we need for an EXE is in the dist\agent directory
    :: zip it up over to our %destdir%
    :: cd into the dist\agent directory and put output into dest.
    CD dist\agent
    IF EXIST %destdir%\client.exe ERASE %destdir%\client.exe
    %zip% a -sfx %destdir%\client.exe * -r > nul
    IF NOT EXIST %destdir%\client.exe CALL :error "problem generating EXE" & GOTO :EOF
    CD ..\..

    ECHO Cleaning up ...
    :: clean up, remove build, log files, warnings and the dist folder too.
    RMDIR build /q/s
    ERASE log*.log
    ERASE warn*.txt
    RMDIR dist /s/q

    GOTO :eof

:oldmain
	@echo off
	:: buildclient.cmd - builds the cilent.zip file.
	::
	:: %1 is our desination folder for client.exe
	set destzip=%temp%\client%random%.7z
	set defdest=..\fishtankserver\download
        set host=None
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
	
        :: check for the server address (Http://IP:port)
        IF x%2==x (
            ECHO You need to specify the IP of the tracker as the second parameter
            GOTO :eof
        ) ELSE (
            set host = %2
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
	:: add Python, we have python already configured the way we want it.
	ECHO python pre-configured....
	%zip% a -r %destzip% misc\python > nul
	
	GOTO :eof

:copyclient
	:: Copy our client files to the lib directory
	ECHO   Main client\ files...
	%zip% a -r %destzip% client\* > nul
	ECHO   register.py
	%zip% a %destzip% register.py > nul
	ECHO   backuptest.py
	%zip% a %destzip% backuptest.py > nul
	ECHO   runclient.cmd
	%zip% a %destzip% runclient.cmd > nul
	ECHO   installclient.cmd
	%zip% a %destzip% installclient.cmd > nul
	ECHO   agent.py
	%zip% a %destzip% agent.py > nul

	GOTO :eof

:copysettings
	ECHO Settings...
	::COPY settings.txt %destdir% > nul
        ECHO [settings] > settings.example
        ECHO .registerurl = /manager/register/ >> settings.example
        ECHO .settingurl = /manager/setting/ >> settings.example
::        FOR /F "tokens=1" %%i in ('python buildclient.py') do echo .managerhost = %%i >> settings.example
        ECHO .managerhost = %host% >> settings.example
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
        
:error
    ECHO %1
    PAUSE
    
    GOTO :eof

        
:end
    ECHO commplete