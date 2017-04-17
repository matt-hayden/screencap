from setuptools import setup

setup(name='screencap',
      use_vcs_version=True,
      description='Simple screen capture and montage',
      url='http://github.com/matt-hayden/screencap',
	  maintainer="Matt Hayden",
	  maintainer_email="github.com/matt-hayden",
      license='Unlicense',
      packages=find_packages(),
	  entry_points = {
	    'console_scripts': ['screencap=screencap.cli:main'],
	  },
	  # TODO: ImageMagick and ffmpeg requirements are outside Python
      install_requires=[
		"tqdm >= 4.10",
      ],
      zip_safe=True,
	  setup_requires = [ "setuptools_git >= 1.2", ]
     )
