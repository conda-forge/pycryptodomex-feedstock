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
        assert re.search(re.compile(libname), os.fsdecode(lsof_out))

    if psutil.LINUX:
        pid = os.getpid()
        try:
            p = psutil.Process(pid)
            found_in_procfs = any(bool(re.match(libname, x.path)) for x in p.memory_maps())
        except:
	    # https://github.com/giampaolo/psutil/issues/2430
            with open(f"/proc/{pid}/smaps", "r") as smaps:
               found_in_procfs = re.search(re.compile(libname), smaps.read())

        # https://travis-ci.community/t/procfs-provides-paths-outside-of-container/9525
        if not found_in_procfs:
            # Modified version of https://stackoverflow.com/a/22581592/1005215
            from ctypes import *

            # this struct will be passed as a ponter,
            # so we don't have to worry about the right layout
            class dl_phdr_info(Structure):
              _fields_ = [
                ('padding0', c_void_p), # ignore it
                ('dlpi_name', c_char_p),
                                        # ignore the reset
              ]


            # call back function, I changed c_void_p to c_char_p
            callback_t = CFUNCTYPE(c_int,
                                   POINTER(dl_phdr_info),
                                   POINTER(c_size_t), c_char_p)

            dl_iterate_phdr = CDLL('libc.so.6').dl_iterate_phdr
            # I changed c_void_p to c_char_p
            dl_iterate_phdr.argtypes = [callback_t, c_char_p]
            dl_iterate_phdr.restype = c_int

            def callback(info, size, data):
              fname = os.fsdecode(info.contents.dlpi_name)
              if re.match(libname, fname):
                  return 1
              return 0

            assert dl_iterate_phdr(callback_t(callback), None)
