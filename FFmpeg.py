import os, os.path
import subprocess
import sys
import time

from . import *

stream_encoding = 'UTF-8'
standard_global_options = ['-nostdin', '-skip_frame', 'nokey', '-an']
# see also ['-nostdin', '-f', 'image2', '-vf', "select='eq(pict_type,PICT_TYPE_I)'", '-vsync', '0']

class FFmpegException(Exception):
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
	ffmpeg_executable = 'FFmPEG.EXE'
	ffprobe_executable = 'FFPROBE.EXE'
else:
	ffmpeg_executable, _ = check_version()
	ffprobe_executable, _ = check_version(['ffprobe', 'avprobe'])
debug("ffmpeg is "+ffmpeg_executable)
debug("ffprobe is "+ffprobe_executable)

def parse_output(outs, errs='', returncode=None):
	error_text = [ 'deprecated pixel format used, make sure you did set range correctly',
				 'DTS discontinuity',
				 'Invalid timestamp',
				 'Non-increasing DTS',
				 'VBV buffer size not set, muxing may fail' ]
	def _parse(b, prefix='STDOUT', error_text=error_text, encoding=stream_encoding):
		lastframeline = ''
		line = b.decode(encoding).rstrip()
		if 'Unrecognized option' in line:
			raise FFmpegException(line)
		elif 'At least one output file must be specified' in line:
			raise FFmpegException(line)
		elif 'Error opening filters!' in line:
			raise FFmpegException(line)
		elif 'Output file is empty, nothing was encoded' in line:
			if lastframeline: error(lastframeline) #
			raise FFmpegException(line)
		elif 'Press [q] to stop, [?] for help' in line:
			error('Running interactive (maybe try -nostdin if using ffmpeg later than the avconv fork)')
		elif line.startswith('frame='): # progress
			lastframeline = line
		else:
			for w in error_text:
				if w in line:
					warning(line)
					break
			else:
				debug(prefix+' '+line)
		return(lastframeline) # progress bar
	if errs:
		for b in errs.splitlines():
			_parse(b, prefix='STDERR')
	#for b in outs.splitlines(): # FFmpeg doesn't believe in stdout
	#	_parse(b)
	return returncode or 0
def ffmpeg(commands, **kwargs):
	timeout = kwargs.pop('timeout', 10*60)
	kwargs['stderr'] = subprocess.PIPE
	debug(" ".join(["Running", ffmpeg_executable]+list(commands)) )
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
	ffmpeg(standard_global_options+['-i', input_file, '-vf', "tile", '-frames:v', '1', '-vsync', '0', output_file], **kwargs)
	try:
		if not os.path.getsize(output_file):
			raise FFmpegException()
	except:
		raise FFmpegException()
	return output_file

def thumbnails(input_file, output_file_pattern=None, options=['-vf', 'scale=160:-1'], **kwargs):
	"""Still captures from each I-frame into a series of files

	input_file
	output_file_pattern:	%08d in this string is replaced with order number
	options:	['-vf', 'scale=160:-1'] resizes images
	"""
	assert os.path.isfile(input_file)
	if 'timeout' not in kwargs:
		kwargs['timeout'] = os.path.getsize(input_file) / 5E6
	if not output_file_pattern:
		output_file_pattern = input_file+'.screen_%04d.PNG'
	output_dir, _ = os.path.split(output_file_pattern)
	st = time.time()
	#ffmpeg(['-nostdin', '-an', '-i', input_file, '-vf', "select='eq(pict_type,PICT_TYPE_I)'", '-vsync', '0', output_file_pattern], **kwargs)
	ffmpeg_commands = standard_global_options \
					  +['-i', input_file] \
					  +options \
					  +['-vsync', '0', output_file_pattern]
	ffmpeg(ffmpeg_commands, **kwargs)
	output_files = [ os.path.join(output_dir, f) for f in os.listdir(output_dir) ]
	new_files = sorted(f for f in output_files if st < os.path.getmtime(f))
	#
	if not new_files:
		info("ffmpeg {ffmpeg_commands} generated nothing, trying harder".format(**locals()) )
		ffmpeg_commands = ['-nostdin', \
						   '-i', input_file, \
						   '-f', 'image2', \
						   '-vf', "select='eq(pict_type,PICT_TYPE_I)'"] \
						  +options \
						  +['-vsync', 'vfr', output_file_pattern]
		ffmpeg(ffmpeg_commands, **kwargs)
		output_files = [ os.path.join(output_dir, f) for f in os.listdir(output_dir) ]
		new_files = sorted(f for f in output_files if st < os.path.getmtime(f))
	if not new_files:
		info("ffmpeg {ffmpeg_commands} generated nothing, trying much harder".format(**locals()) )
		ffmpeg_commands = ['-nostdin', \
						   '-i', input_file, \
						   '-f', 'image2', \
						   '-vf', 'fps=1/240'] \
						  +options \
						  +[output_file_pattern]
		ffmpeg(ffmpeg_commands, **kwargs)
		output_files = [ os.path.join(output_dir, f) for f in os.listdir(output_dir) ]
		new_files = sorted(f for f in output_files if st < os.path.getmtime(f))
	if not new_files:
		info("ffmpeg {ffmpeg_commands} generated nothing, trying desperately".format(**locals()) )
		ffmpeg_commands = ['-nostdin', \
						   '-i', input_file, \
						   '-f', 'image2', \
						   '-vframes', '1'] \
						  +options \
						  +[output_file_pattern]
		ffmpeg(ffmpeg_commands, **kwargs)
		output_files = [ os.path.join(output_dir, f) for f in os.listdir(output_dir) ]
		new_files = sorted(f for f in output_files if st < os.path.getmtime(f))
	if not new_files:
		error("ffmpeg {ffmpeg_commands} generated nothing".format(**locals()) )
		return []
	#
	n = len(new_files)
	dur = time.time() - st
	debug("Wrote {:d} images in {:.0f} s, averaging {:.1f}".format(n, dur, (dur/n) if n else dur))
	# using % notation, a-la ffmpeg
	if (output_file_pattern % 1) in new_files and (output_file_pattern % n) in new_files:
		return (output_file_pattern % x for x in range(1, n+1))
	else:
		return new_files

