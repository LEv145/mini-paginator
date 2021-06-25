import setuptools
with open("README.md", encoding="utf8") as f:
    long_description = f.read()
with open("requirements.txt", encoding="utf8") as f:
    requirements = f.readlines()
setuptools.setup(
    name="mini_paginator",
    version="1.2.3",
    author="Lev145",
    description="Mini-paginator for discord.py",
    long_description=long_description,
    url="https://github.com/LEv145/mini-paginator",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)
