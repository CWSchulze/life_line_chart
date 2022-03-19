import shutil
import sys
from setuptools import setup
import versioneer

if 'clean' in sys.argv:
    try:
        shutil.rmtree('build')
    except Exception:
        pass
    try:
        shutil.rmtree('dist')
    except Exception:
        pass

cmdclass = versioneer.get_cmdclass()
setup(
    cmdclass=cmdclass,
    name="life_line_chart",
    version=versioneer.get_version(),
    author="Christian Schulze",
    author_email="c.w.schulze@gmail.com",
    description=("Generate ancestor (genealogy) chart"),
    description_content_type='text/plain',
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    license="MIT License",
    keywords="genealogy, gedcom, chart, ancestors",
    url="https://github.com/CWSchulze/life_line_chart",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    platforms="OS Independent",
    # package_data={'life_line_chart': ['ringe.png']},
    data_files=[('life_line_chart', [
        'life_line_chart/ringe.png',
        'life_line_chart/AncestorChartStrings.json',
        'life_line_chart/DescendantChartStrings.json',
        'life_line_chart/BaseChartStrings.json'
    ])],
    include_package_data=True,
    packages=['life_line_chart'],
    extras_require={
        "photo_tests": ["pillow"],
        "data_generator": ["names"],
    },
    install_requires=['svgwrite'],
    ext_modules=[]
)

# to build enter:
# python setup.py bdist_wheel

# to upload to pypi
# python setup.py sdist
# twine upload
