import process as pkg
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    readme = fh.read()

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
        "Programming Language :: Python :: 3",
        'License :: OSI Approved :: Apache Software License',
        'Framework :: Django',
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
