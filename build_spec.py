# -*- mode: python -*- 
block_cipher = None 
ECHO is off.
# Collect all icon files 
icon_files = [ 
   ('icons\folder.png', 'icons'
   ('icons\collapsed.png', 'icons'
   ('icons\expanded.png', 'icons'
   ('icons\down_arrow.png', 'icons'
   ('icons\checkmark.png', 'icons'
   ('icons\oblivion.png', 'icons'
] 
ECHO is off.
# Collect all data files 
data_files = [ 
   ('data\all books and scrolls ids.json', 'data'
   ('data\all clothing_ amulets_ and rings ids.json', 'data'
   ('data\all horses ids.json', 'data'
   ('data\all keys ids.json', 'data'
   ('data\all locations ids.json', 'data'
   ('data\all miscellaneous ids.json', 'data'
   ('data\all npc ids.json', 'data'
   ('data\all potions and drinks ids.json', 'data'
   ('data\all quest commands.json', 'data'
   ('data\all sigil stone ids.json', 'data'
   ('data\all soul gems ids.json', 'data'
   ('data\all spells ids.json', 'data'
   ('data\all toggle commands.json', 'data'
   ('data\all weapons ids.json', 'data'
   ('data\target commands.json', 'data'
   ('data\useful cheats.json', 'data'
   ('data\all alchemy equipment ids.json', 'data'
   ('data\all alchemy ingredients ids.json', 'data'
   ('data\all armor ids.json', 'data'
   ('data\all arrow ids.json', 'data'
] 
ECHO is off.
a = Analysis(['app.py'], 
    pathex=[], 
    binaries=[], 
    datas=[('styles.qss', '.')] + icon_files + data_files, 
    hiddenimports=['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.sip', 'pyautogui', 'psutil', 'json_loader', 'game_connector', 'ui_builder', 'enhanced_ui_main'], 
    hookspath=[], 
    hooksconfig={}, 
    runtime_hooks=[], 
    excludes=['PyQt5', 'PySide2', 'PySide6'], 
    win_no_prefer_redirects=False, 
    win_private_assemblies=False, 
    cipher=block_cipher, 
    noarchive=False, 
) 
ECHO is off.
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher) 
ECHO is off.
exe = EXE(pyz, 
    a.scripts, 
    a.binaries, 
    a.zipfiles, 
    a.datas, 
    [], 
    name='Oblivion Console Manager', 
    debug=False, 
    bootloader_ignore_signals=False, 
    strip=False, 
    upx=True, 
    upx_exclude=[], 
    runtime_tmpdir=None, 
    console=False, 
    disable_windowed_traceback=False, 
    argv_emulation=False, 
    target_arch=None, 
    codesign_identity=None, 
    entitlements_file=None, 
    icon='icons/oblivion.png', 
) 
