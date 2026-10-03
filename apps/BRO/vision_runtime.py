"""Restore the child interpreter's package path after multiprocessing spawn."""
import site
import sys
import sysconfig

def restore_packages():
    # spawn copies the parent sys.path, replacing the venv's site-packages.
    # Keep the app paths, but put this interpreter's own packages first.
    if sys.prefix!=sys.base_prefix:
        packages=sysconfig.get_path('purelib')
        site.addsitedir(packages)
        if packages in sys.path:sys.path.remove(packages)
        sys.path.insert(0,packages)
