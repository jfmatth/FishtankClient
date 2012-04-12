# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'agentservice.py'],
             pathex=['C:\\Users\\john\Development\\FishtankClient'])
b = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'register.py'],
             pathex=['C:\\Users\\john\\Development\\FishtankClient'])
pyz = PYZ(a.pure + b.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\agent', 'agentservice.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=True )
exe2 = EXE(pyz,
          b.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\agent', 'register.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=True )

coll = COLLECT( exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               exe2,
               b.binaries,
               b.zipfiles,
               b.datas,
               strip=False,
               upx=True,
               name=os.path.join('dist', 'agent'))
