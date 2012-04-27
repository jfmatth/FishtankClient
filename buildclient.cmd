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
