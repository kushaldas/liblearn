import os
import sys
import shutil
import subprocess

try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    bdist_wheel = None

from setuptools import setup, find_packages
from distutils.command.build_py import build_py
from distutils.command.build_ext import build_ext
from setuptools.dist import Distribution


# Build with clang if not otherwise specified.
if os.environ.get('LIBLEARN_MANYLINUX') == '1':
    os.environ.setdefault('CC', 'gcc')
    os.environ.setdefault('CXX', 'g++')
else:
    os.environ.setdefault('CC', 'clang')
    os.environ.setdefault('CXX', 'clang++')


PACKAGE = 'liblearn'
EXT_EXT = sys.platform == 'darwin' and '.dylib' or '.so'


def build_liblearn(base_path):
    lib_path = os.path.join(base_path, '_liblearn.so')
    here = os.path.abspath(os.path.dirname(__file__))
    cmdline = ['cargo', 'build', '--release']
    if not sys.stdout.isatty():
        cmdline.append('--color=always')
    rv = subprocess.Popen(cmdline, cwd=here).wait()
    if rv != 0:
        sys.exit(rv)
    src_path = os.path.join(here, 'target', 'release',
                            'libliblearn' + EXT_EXT)
    if os.path.isfile(src_path):
        shutil.copy2(src_path, lib_path)


class CustomBuildPy(build_py):
    def run(self):
        build_py.run(self)
        build_liblearn(os.path.join(self.build_lib, *PACKAGE.split('.')))


class CustomBuildExt(build_ext):
    def run(self):
        build_ext.run(self)
        if self.inplace:
            build_py = self.get_finalized_command('build_py')
            build_liblearn(build_py.get_package_dir(PACKAGE))


class BinaryDistribution(Distribution):
    """This is necessary because otherwise the wheel does not know that
    we have non pure information.
    """
    def has_ext_modules(foo):
        return True


cmdclass = {
    'build_ext': CustomBuildExt,
    'build_py': CustomBuildPy,
}


# The wheel generated carries a python unicode ABI tag.  We want to remove
# this since our wheel is actually universal as far as this goes since we
# never actually link against libpython.  Since there does not appear to
# be an API to do that, we just patch the internal function that wheel uses.
if bdist_wheel is not None:
    class CustomBdistWheel(bdist_wheel):
        def get_tag(self):
            rv = bdist_wheel.get_tag(self)
            return ('py2.py3', 'none') + rv[2:]
    cmdclass['bdist_wheel'] = CustomBdistWheel


setup(
    name='liblearn',
    version='0.1.0',
    url='http://github.com/kushaldas/liblearn',
    description='Module to learn writing Python extensions in rust',
    license='BSD',
    author='kushal',
    author_email='kushaldas@gmail.com',
    packages=find_packages(),
    cffi_modules=['build.py:ffi'],
    cmdclass=cmdclass,
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'cffi>=1.6.0',
    ],
    setup_requires=[
        'cffi>=1.6.0'
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    ext_modules=[],
    distclass=BinaryDistribution
)

