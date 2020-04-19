import setuptools
from glob import glob
#classifiers: https://pypi.org/pypi?%3Aaction=list_classifiers
import shutil, os, sys

from distutils.core import setup
import shutil
import sys



def read_version(filename):
    import re
    content = open(filename).read()
    version_numbers = re.findall('__version__\\s*=\\s*[\'"]([^\'"]+)[\'"]', content)
    return version_numbers[0]
__version__ = read_version('life_line_chart/__init__.py')


try:
    shutil.rmtree('build')
except:
    pass

cmdclass = {}
setup(
    cmdclass=cmdclass,
    name="life_line_chart",
    version=__version__,
    author="Christian Schulze",
    author_email="c.w.schulze@gmail.com",
    description = ("Generate ancestor (genealogy) chart"),
    license = open('LICENSE','r').read(),
    keywords = "genealogy, gedcom, chart, ancestors",
    #url = "https://www.tlk-thermo.com/index.php/en/dave",
    classifiers = [
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Natural Language :: German",
        "Topic :: Scientific/Engineering",
    ],
    platforms=['all'],
    #scripts=['life_line_chart_gui.py'],
    package_data={'life_line_chart': ['*.png']},
    include_package_data=True,
    packages=setuptools.find_packages(),

    install_requires=['numpy','svgwrite','svgpathtools'],
    ext_modules=[]

)

# to build enter:
# python setup.py bdist_wheel