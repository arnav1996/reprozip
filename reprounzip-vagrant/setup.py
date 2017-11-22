import io
import os
from setuptools import setup


# pip workaround
os.chdir(os.path.abspath(os.path.dirname(__file__)))


# Need to specify encoding for PY3, which has the worst unicode handling ever
with io.open('README.rst', encoding='utf-8') as fp:
    description = fp.read()
setup(name='reprounzip-vagrant',
      version='1.0.10',
      packages=['reprounzip', 'reprounzip.unpackers',
                'reprounzip.unpackers.vagrant'],
      entry_points={
          'reprounzip.unpackers': [
              'vagrant = reprounzip.unpackers.vagrant:setup']},
      namespace_packages=['reprounzip', 'reprounzip.unpackers'],
      install_requires=[
          'reprounzip>=1.0.10',
          'rpaths>=0.8',
          'paramiko'],
      description="Allows the ReproZip unpacker to create virtual machines",
      author="Remi Rampin, Fernando Chirigati, Dennis Shasha, Juliana Freire",
      author_email='reprozip-users@vgc.poly.edu',
      maintainer="Remi Rampin",
      maintainer_email='remirampin@gmail.com',
      url='http://vida-nyu.github.io/reprozip/',
      long_description=description,
      license='BSD-3-Clause',
      keywords=['reprozip', 'reprounzip', 'reproducibility', 'provenance',
                'vida', 'nyu', 'vagrant'],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Topic :: Scientific/Engineering',
          'Topic :: System :: Archiving'])
