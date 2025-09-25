#!/usr/bin/env python3
"""
Setup script for hdr10plus_gen - Dolby Vision RPU to HDR10+ converter
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="hdr10plus_gen",
    version="1.0.0",
    author="HDR10+ Generator Team",
    author_email="team@hdr10plus-gen.com",
    description="Convert Dolby Vision RPU data to HDR10+ dynamic metadata",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hdr10plus-gen/hdr10plus_gen",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "hdr10plus_gen=hdr10plus_gen.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "hdr10plus_gen": [
            "schemas/*.json",
            "test_data/*.rpu",
            "test_data/*.json",
        ],
    },
)