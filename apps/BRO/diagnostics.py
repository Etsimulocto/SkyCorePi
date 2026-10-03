"""Read-only host diagnostics; does not probe buses or seize USB/camera ports."""
import importlib.util
import platform
import shutil
import glob
from pathlib import Path

def report():
    from backend import ROOT,SPEAKERS
    return '\n'.join(['SkyCorePi / BRO diagnostics',platform.platform(),'Python '+platform.python_version(),
        'Dependencies: '+', '.join(name+(' OK' if importlib.util.find_spec(name) else ' MISSING') for name in ('serial','cv2','tkinter')),
        'Ollama executable: '+str(shutil.which('ollama')),
        'Video nodes: '+', '.join(glob.glob('/dev/video*')),
        'USB serial nodes: '+', '.join(glob.glob('/dev/ttyACM*')),
        'Identity cards: '+', '.join(name+(' OK' if (ROOT/'characters'/(name.lower()+'.json')).exists() else ' MISSING') for name in SPEAKERS if name!='BRO'),
        'Archive: '+('present' if Path('/home/quarterbitgames/Bloomcore/GitHub/spiralside').exists() else 'not found'),
        'Board diagnostic core: not implemented; current BloomFace protocol 1'])
