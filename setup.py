import os
import process as pkg
import sys
from pip._internal.req import parse_requirements
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    readme = fh.read()

if sys.argv[-1] == 'pypi-publish':
    os.system("python setup.py sdist") and sys.exit(1)
    os.system("twine upload dist/*") and sys.exit(1)
    sys.exit()

setup(
    name=pkg.__title__,
    version=pkg.__version__,
    author=pkg.__author__,
    author_email=pkg.__author_email__,
    description=pkg.__description__,
    long_description=readme,
    long_description_content_type="text/markdown",
    url=pkg.__url__,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration"
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['django']
)
