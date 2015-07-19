import os, os.path
import subprocess
import sys
import time

#from . import *
def debug(*args, **kwargs):
	pass
info=debug
warning=error=critical=print

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
	warnings = [ 'deprecated pixel format used, make sure you did set range correctly',
				 'DTS discontinuity',
				 'Invalid timestamp',
				 'Non-increasing DTS',
				 'VBV buffer size not set, muxing may fail' ]
	def _parse(b, prefix='STDOUT', warnings=warnings, encoding='ASCII'):
		lastframeline = ''
		line = b.decode(encoding).rstrip()
		if 'Unrecognized option' in line:
			raise FFMpegException(line)
		elif 'At least one output file must be specified' in line:
			raise FFMpegException(line)
		elif 'Error opening filters!' in line:
			raise FFMpegException(line)
		elif 'Output file is empty, nothing was encoded' in line:
			if lastframeline: error(lastframeline) #
			raise FFMpegException(line)
		elif 'Press [q] to stop, [?] for help' in line:
			error('Running interactive (maybe try -nostdin if using ffmpeg later than the avconv fork)')
		elif line.startswith('frame='): # progress
			lastframeline = line
		else:
			for w in warnings:
				if w in line:
					warning(line)
					break
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
	return output_file

def thumbnails(input_file, output_file_pattern=None, **kwargs):
	"""Still captures from each I-frame into a series of files
	"""
	if 'timeout' not in kwargs:
		kwargs['timeout'] = os.path.getsize(input_file) / 5E6
	if not output_file_pattern:
		output_file_pattern = input_file+'.screen_%04d.PNG'
	output_dir, _ = os.path.split(output_file_pattern)
	st = time.time()
	#ffmpeg(['-nostdin', '-an', '-i', input_file, '-vf', "select='eq(pict_type,PICT_TYPE_I)'", '-vsync', '0', output_file_pattern], **kwargs)
	ffmpeg(['-nostdin', '-skip_frame', 'nokey', '-an', '-i', input_file, '-vf', 'scale=160:-1', '-vsync', '0', output_file_pattern], **kwargs)
	output_files = (os.path.join(output_dir, f) for f in os.listdir(output_dir))
	new_files = sorted(f for f in output_files if st < os.path.getmtime(f))
	n = len(new_files)
	if (output_file_pattern % 1) in new_files and (output_file_pattern % n) in new_files:
		return (output_file_pattern % x for x in range(1, n+1))
	else:
		return new_files

