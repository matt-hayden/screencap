import os, os.path
import subprocess

def montage(input_files, options=[], output_filename=None, **kwargs):
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
	returncode = subprocess.check_call(['montage.im6']+input_files+options+[output_filename])
	assert not returncode
	return output_filename

