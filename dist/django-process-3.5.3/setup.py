import process
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="django-process",
    version=process.__version__,
    author="Josue Gomez",
    author_email="jgomez@binkfe.com",
    description="A package for create process and tasks on django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.binkfe.com/jesrat/django-process",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        'Framework :: Django',
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
