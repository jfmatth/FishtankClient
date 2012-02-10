:main
	PUSHD misc
	
::	start /wait python-2.6.6.msi /qb TARGETDIR=%cd%\python ALLUSERS=0 ADDLOCAL=DefaultFeature
::	IF NOT %errorlevel%==0 GOTO error
	start /wait vcredist_x86.exe /q
	IF NOT %errorlevel%==0 GOTO error
::	:: move Crypto to site-packages.
::	MOVE Crypto PYTHON\LIB\SITE-PACKAGES
	:: get rid of any firewall issues. XP for now
	NETSH FIREWALL ADD allowedprogram %cd%\python\python.exe Fishtank ENABLE	
	POPD
	move settings.example settings.txt
	
	GOTO end
:error
	ECHO Error installing.
	PAUSE
:end