import os,sys
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop


_here = os.path.abspath(os.path.dirname(__file__))
#dir_mtree = os.path.join(_here,'metricaltree')

README_CONFIG="""# PROSODIC HOME DIRECTORY
This is your home directory for Prosodic. [https://github.com/quadrismegistus/prosodic].

## Configuration
* In order to configure Prosodic, copy or rename 'config_default.py' to 'config.py', and edit that file according to its instructions.
* [Note: 'config_default.py' will be overwritten if you update Prosodic, but 'config.py' will not be.]

## Meters
* To edit or create your own meter, copy or rename 'meters/meter_default.py' to 'meters/your_meter_name.py', and edit that file according to its instructions.
* Then consider changing the default 'meter' setting in your config.py to 'your_meter_name'.
* You can also select 'your_meter_name' from within Prosodic.
* [Note: 'meters/meter_default.py' will be overwritten if you update Prosodic, but 'meters/your_meter_name.py' will not be.]

## Tagged samples
* To run Prosodic against your own tagged sample, create a file like 'tagged_samples/tagged-sample-litlab-2016.txt', which has at least a column for the line (e.g. "From fairest creatures we desire increase") and a column for the parse (e.g. "wswswswsws").
* [Note: 'tagged_samples/tagged-sample-litlab-2016.txt' will be overwritten if you update Prosodic, but your own files will not be.]

## Results
* By default, results will be saved to the 'results' folder here.
* You can change this option in the 'folder_results' option in 'config.py'.

## Corpora and texts
* By default, Prosodic will look for texts within the 'corpora' folder here.
* You can change this option in the 'folder_corpora' option in config.py.

## Etc
* For more information, see Prosodic's website @ https://github.com/quadrismegistus/prosodic
"""


def configure_home_dir():
	# def copytree(src, dst, symlinks=False, ignore=None):
	# 	for item in os.listdir(src):
	# 		s = os.path.join(src, item)
	# 		d = os.path.join(dst, item)
	# 		if os.path.isdir(s):
	# 			shutil.copytree(s, d, symlinks, ignore)
	# 		else:
	# 			shutil.copy2(s, d)


	# make sure directory exists
	from os.path import expanduser
	home = expanduser("~")
	dir_prosodic_home=os.path.join(home,'prosodic_data')
	dir_meter_home=os.path.join(dir_prosodic_home,'meters')
	for dir in [dir_prosodic_home,dir_meter_home]:
		if not os.path.exists(dir): os.makedirs(dir)

	# get paths
	ipath_config = os.path.join(_here,'prosodic','config.py')
	ipath_meter = os.path.join(_here,'prosodic','meters','meter_default.py')
	ipath_samples = os.path.join(_here,'prosodic','tagged_samples')
	ipath_corpora = os.path.join(_here,'prosodic','corpora')

	opath_config = os.path.join(dir_prosodic_home,'config_default.py')
	opath_meter = os.path.join(dir_meter_home,'meter_default.py')
	opath_samples = os.path.join(dir_prosodic_home,'tagged_samples')
	opath_results = os.path.join(dir_prosodic_home,'results')
	opath_corpora = os.path.join(dir_prosodic_home,'corpora')

	# make folders
	for odir in [opath_samples,opath_results,opath_corpora]:
		if not os.path.exists(odir):
			os.makedirs(odir)

	# copy
	import shutil
	print '>> copying:',ipath_config,'-->',opath_config
	shutil.copyfile(ipath_config,opath_config)
	print '>> copying:',ipath_meter,'-->',opath_meter
	shutil.copyfile(ipath_meter,opath_meter)

	# copy samples
	for fn in os.listdir(ipath_samples):
		if fn.startswith('.'): continue
		ifnfn=os.path.join(ipath_samples,fn)
		ofnfn=os.path.join(opath_samples,fn)
		print '>> copying:',ifnfn,'-->',ofnfn
		shutil.copyfile(ifnfn,ofnfn)

	# copy corpora
	from distutils.dir_util import copy_tree
	copy_tree(ipath_corpora,opath_corpora)

	# write README
	with open(os.path.join(dir_prosodic_home,'README.txt'),'w') as of:
		of.write(README_CONFIG)

	# save other README
	shutil.copyfile(os.path.join(_here,'README.md'),'README_prosodic.txt')


class PostDevelopCommand(develop):
	"""Post-installation for development mode."""
	def run(self):
		configure_home_dir()
		develop.run(self)

class PostInstallCommand(install):
	"""Post-installation for installation mode."""
	def run(self):
		configure_home_dir()
		install.run(self)

with open("README.md", "r") as fh:
	long_description = fh.read()

with open("requirements.txt", "r") as fh:
	requirements = [x.strip() for x in fh.read().split('\n') if x.strip()]

setup(
	name='prosodic',
	version='1.2.1',
	description=('PROSODIC: a metrical-phonological parser, written in Python. For English and Finnish, with flexible language support.'),
	long_description=long_description,
	long_description_content_type="text/markdown",
	author='Ryan Heuser',
	author_email='heuser@stanford.edu',
	url='https://github.com/quadrismegistus/prosodic',
	license='MPL-2.0',
	packages=['prosodic','metricaltree'],
	install_requires=requirements,
	include_package_data=True,
	cmdclass={
		'develop': PostDevelopCommand,
		'install': PostInstallCommand,
	},
	scripts=['bin/prosodic'],
	classifiers=[
		#'Development Status :: 3 - Alpha',
		#'Intended Audience :: Science/Research',
		#'Programming Language :: Python :: 2.7',
		#'Programming Language :: Python :: 3.6'
	],
	)
