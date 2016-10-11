import subprocess
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules=[
            Extension("libmsgq",             ["lib/libmsgq.py"]),
            Extension("libsyn",              ["lib/libsyn.py"]),
            Extension("syngularity",         ["src/syngularity.py"]),
]

setup(
          name = 'syngularity',
            cmdclass = {'build_ext': build_ext},
              ext_modules = ext_modules,
)

subprocess.Popen('mkdir -p ./shared', stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
subprocess.Popen('mkdir -p ./bin', stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
subprocess.Popen('mv *.so ./shared', stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
subprocess.Popen('mv lib/*.so ./shared', stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
subprocess.Popen('mv lib/*.c ./shared', stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
subprocess.Popen('mv src/*.so ./shared', stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
subprocess.Popen('mv src/*.c ./shared', stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
subprocess.Popen('rm -rf ./build', stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)

wrapper = """#! /usr/bin/python
import sys
sys.path.append('../shared')
import syngularity

syngularity.constructor()"""
with open('./bin/syngularity', 'w') as f:
    f.write(wrapper)

subprocess.Popen('chmod 755 ./bin/syngularity', stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
