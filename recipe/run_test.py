import os
import re
import psutil
import platform
import subprocess

libname = re.escape(os.environ['CONDA_PREFIX']) + '.*(libgmp.*.(dylib|so))'

# Support for MPIR was removed in 3.4.8 in favour of native C extension
# https://github.com/Legrandin/pycryptodome/issues/114
# https://github.com/Legrandin/pycryptodome/blob/v3.6.3x/lib/Crypto/Math/_Numbers_gmp.py#L98-L99

if not psutil.WINDOWS:
    # The import below will fail if we don't have gmp (on unix)
    from Cryptodome.Math import _IntegerGMP as IntegerGMP

    # Make sure that gmp is indeed loaded in memory
    if psutil.MACOS:
        lsof_out = subprocess.check_output(['lsof', '-p', str(os.getpid())])
        assert re.search(re.compile(libname), lsof_out.decode('utf-8'))

    if psutil.LINUX:
        p = psutil.Process(os.getpid())
        print(len(p.memory_maps()))
        for x in p.memory_maps():
            print(x.path)
        assert any(bool(re.match(libname, x.path)) for x in p.memory_maps())
