import os, os.path
import subprocess

def montage(input_files, options=[], output_file=None, **kwargs):
	if not output_file:
		f, x = os.path.splitext(input_files[0])
		output_file = f+'_montage'+x
	for k, v in kwargs.items():
		if v is True: # special value
			options += [ '-'+k ]
		elif v is False: # special value
			assert '-'+k in options
			options.remove('-'+k)
		else:
			options += [ '-'+k, str(v) ]
	assert not os.path.exists(output_file)
	returncode = subprocess.check_call(['montage.im6']+input_files+options+[output_file])
	assert not returncode
	return output_file

