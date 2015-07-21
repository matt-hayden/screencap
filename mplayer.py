import subprocess
import sys

from . import *

def check_version(executables=['mplayer']):
	for e in executables:
		try:
			version_string = subprocess.check_output([e, '-version'])
			return (e, version_string)
		except OSError:
			pass
	raise OSError()

if sys.platform.startswith('win'):
	mplayer_executable = 'MPLAYER.EXE'
else:
	mplayer_executable, _ = check_version()
debug("mplayer is "+mplayer_executable)
