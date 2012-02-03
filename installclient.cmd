PUSHD misc
start /wait python-2.6.6.msi /qb TARGETDIR=c:\client\misc\python ALLUSERS=1 ADDLOCAL=DefaultFeature
start /wait vcredist_x86.exe /q
POPD
move settings.example settings.txt