#!/usr/bin/env python3
"""
Setup script for EP_annotator package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
if (this_directory / "requirements.txt").exists():
    requirements = (this_directory / "requirements.txt").read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="ep_annotator",
    version="0.1.0",
    author="Your Name",
    author_email="liu.huand@gmail.com",
    description="A bioinformatics tool for annotating enhancer-promoter interactions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Badgerliu/EP_annotator",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ep-annotator=ep_annotator.cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 