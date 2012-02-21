:main
    SET fPYTHON=%CD%\misc\python\python.exe
	PUSHD misc
	
	start /wait vcredist_x86.exe /q
	IF NOT %errorlevel%==0 GOTO error
	:: get rid of any firewall issues. XP for now
	NETSH FIREWALL ADD allowedprogram %cd%\python\python.exe Fishtank ENABLE	
	POPD
	move settings.example settings.txt

	:: register this client
	%fPYTHON% register.py -u 2 -p password
	IF %ERRORLEVEL%==0 %fPYTHON% agent.py

	GOTO end
:error
	ECHO Error installing.
	PAUSE
:end