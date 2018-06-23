import os
import re
import psutil
import platform

libname = re.escape(os.environ['CONDA_PREFIX']) + '.*(libgmp.*.(dylib|so))'

# Support for MPIR was removed in 3.4.8 in favour of native C extension
# https://github.com/Legrandin/pycryptodome/issues/114
# https://github.com/Legrandin/pycryptodome/blob/v3.6.3x/lib/Crypto/Math/_Numbers_gmp.py#L98-L99

if not psutil.WINDOWS:
    # The import below will fail if we don't have gmp (on unix)
    from Cryptodome.Math import _Numbers_gmp as NumbersGMP

    # Make sure that gmp is indeed loaded in memory
    p = psutil.Process(os.getpid())
    assert any(bool(re.match(libname, x.path)) for x in p.memory_maps())
