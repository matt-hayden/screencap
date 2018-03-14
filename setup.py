import os, os.path
from setuptools import find_packages, setup

setup(name='PyScreencap',
      version = "3.0a5",
      description='Simple tiled screencaps of local and remote video',
      url='https://github.com/matt-hayden/screencap',
      maintainer="Matt Hayden (Valenceo, LTD.)",
      maintainer_email="github.com/matt-hayden",
      license='Unlicense',
      packages=find_packages(exclude='contrib docs tests'.split()),
      entry_points = {
          'console_scripts': [
              'screencap=screencap.cli:make_screencaps',
              'm3usplit=screencap.cli:make_split_script',
              'm3u_by_quality=screencap.cli:sort_playlist',
              ]
          },
      package_data = {
          'screencap': ['etc/*'],
          },
      install_requires = [ 'requests' ],
      zip_safe=True,
     )
