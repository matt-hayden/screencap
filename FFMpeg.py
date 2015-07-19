import os, os.path
import subprocess
import sys

#from . import *
debug=info=warning=error=critical=print

class FFMpegException(Exception):
	pass
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

def parse_output(outs, errs='', returncode=None):
	def _parse(b, prefix='STDOUT', encoding='ASCII'):
		lastframeline = ''
		line = b.decode(encoding).rstrip()
		if 'At least one output file must be specified' in line:
			raise FFMpegException(line)
		elif 'Error opening filters!' in line:
			raise FFMpegException(line)
		elif 'Output file is empty, nothing was encoded' in line:
			if lastframeline: error(lastframeline) #
			raise FFMpegException(line)
		elif 'Press [q] to stop, [?] for help' in line:
			error('Running interactive (maybe try -nostdin if using ffmpeg later than the avconv fork)')
		elif 'Non-increasing DTS' in line:
			warning(line)
		elif 'Invalid timestamp' in line:
			warning(line)
		elif 'DTS discontinuity' in line:
			warning(line)
		elif 'VBV buffer size not set, muxing may fail' in line:
			warning(line)
		elif 'deprecated pixel format used, make sure you did set range correctly' in line:
			warning(line)
		elif line.startswith('frame='):
			lastframeline = line
		else:
			debug(prefix+' '+line)
		return(lastframeline) # progress bar
	if errs:
		for b in errs.splitlines():
			_parse(b, prefix='STDERR')
	#for b in outs.splitlines(): # FFMpeg doesn't believe in stdout
	#	_parse(b)
	return returncode or 0
def ffmpeg(commands, **kwargs):
	timeout = kwargs.pop('timeout', 60*10)
	kwargs['stderr'] = subprocess.PIPE
	debug(commands)
	proc = subprocess.Popen([ffmpeg_executable]+list(commands), **kwargs)
	try:
		outs, errs = proc.communicate(timeout=timeout)
	except subprocess.TimeoutExpired:
		proc.kill()
		outs, errs = proc.communicate()
	return parse_output(outs, errs, proc.returncode)
def thumbnail_mosaic(input_file, output_file=None, **kwargs):
	"""Still captures from each I-frame into a single sheet
	"""
	if 'timeout' not in kwargs:
		kwargs['timeout'] = os.path.getsize(input_file) / 5E6 + 5
	if not output_file:
		output_file = input_file+'.screens.jpg'
	#ffmpeg(['-nostdin', '-an', '-i', input_file, '-vf', "select='gt(scene,0.4)',scale=160:120,tile", '-frames:v', '1', output_file], **kwargs)
	#ffmpeg(['-nostdin', '-an', '-i', input_file, '-vf', "select='eq(pict_type,PICT_TYPE_I)',tile", '-frames:v', '1', '-vsync', '0', output_file], **kwargs)
	ffmpeg(['-nostdin', '-skip_frame', 'nokey', '-an', '-i', input_file, '-vf', "tile", '-frames:v', '1', '-vsync', '0', output_file], **kwargs)
	try:
		if not os.path.getsize(output_file):
			raise FFMpegException()
	except:
		raise FFMpegException()

def thumbnails(input_file, output_file_pattern=None, **kwargs):
	"""Still captures from each I-frame into a series of files
	"""
	if 'timeout' not in kwargs:
		kwargs['timeout'] = os.path.getsize(input_file) / 5E6
	if not output_file_pattern:
		output_file_pattern = input_file+'.screen_%04d.jpg'
	#ffmpeg(['-nostdin', '-an', '-i', input_file, '-vf', "select='eq(pict_type,PICT_TYPE_I)'", '-vsync', '0', output_file_pattern], **kwargs)
	ffmpeg(['-nostdin', '-skip_frame', 'nokey', '-an', '-i', input_file, '-vsync', '0', output_file_pattern], **kwargs)
	try:
		if not os.path.getsize(output_file_pattern % 1):
			raise FFMpegException()
	except:
		raise FFMpegException()

