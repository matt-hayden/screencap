import subprocess
import sys

#from . import *
debug=print

def check_version(executables=['ffmpeg', 'avconv']):
	for e in executables:
		try:
			version_string = subprocess.check_output([e, '-version'])
			return (e, version_string)
		except OSError:
			pass
	raise OSError()

if sys.platform.startswith('win'):
	ffmpeg_executable = 'FFMPEG.EXE'
	ffprobe_executable = 'FFPROBE.EXE'
else:
	ffmpeg_executable, _ = check_version()
	ffprobe_executable, _ = check_version(['ffprobe', 'avprobe'])
debug("ffmpeg is "+ffmpeg_executable)
debug("ffprobe is "+ffprobe_executable)
