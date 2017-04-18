
import os, os.path
import subprocess

try:
	from . import debug, info, warning, error, fatal
except:
	debug = info = warning = error = fatal = print


stream_encoding = 'UTF-8'

montage_executable = 'montage.im6'
montage_executable = 'montage'

class ImageMagickException(Exception):
	pass
def montage(input_files, output_filename=None, options=[], **kwargs):
	class MontageException(ImageMagickException):
		pass
	def _parse(b, prefix='STDOUT', encoding=stream_encoding):
		'''Example errors:
		montage.im6: unable to open image `...': File name too long @ error/blob.c/OpenBlob/2638.
		'''
		line = b.decode().rstrip()
		if 'unable to open image' in line:
			raise MontageException(line)
		else:
			debug(line)
	if not output_filename:
		f, x = os.path.splitext(input_files[0])
		output_filename = f+'_montage'+x
	for k, v in kwargs.items():
		if v is True: # special value
			options += [ '-'+k ]
		elif v is False: # special value
			assert '-'+k in options
			options.remove('-'+k)
		else:
			options += [ '-'+k, str(v) ]
	proc = subprocess.Popen([montage_executable]+input_files+options+[output_filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	outs, _ = proc.communicate()
	rc = proc.returncode
	for b in outs.splitlines():
		_parse(b, prefix='')
	if not rc:
		debug("montage exited successfully")
	else:
		raise MontageException("montage exited {}".format(rc))
	return output_filename

