import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-process",
    version="3.1",
    author="Josue Gomez",
    author_email="jgomez@binkfe.com",
    description="A package for create process and tasks on django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.binkfe.com/jesrat/django-process",
    packages=[
        'process',
        'process.management',
        'process.management.commands',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        'Framework :: Django',
        "Operating System :: OS Independent",
    ],
)
