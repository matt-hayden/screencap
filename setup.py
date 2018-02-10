from setuptools import find_packages, setup

setup(name='PyScreencap',
      version = "3.0a1",
      description='Simple tiled screencaps of local and remote video',
      url='https://github.com/matt-hayden/screencap',
      maintainer="Matt Hayden (Valenceo, LTD.)",
      maintainer_email="github.com/matt-hayden",
      license='Unlicense',
      packages=find_packages(),
      entry_points = {
          'console_scripts': [
              'screencap=screencap.cli:main',
              ]
      },
      zip_safe=True # but, ffmpeg and convert-im6 need to be on the system
     )
