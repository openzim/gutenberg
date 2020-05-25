#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" Project Gutemberg ZIM creator for Offline Use """

from codecs import open

from setuptools import setup, find_packages

from gutenbergtozim import VERSION

with open("pypi-readme.rst", "r", "utf-8") as f:
    readme = f.read()

with open("requirements.pip", "r") as f:
    requirements = [l.strip() for l in f.readlines() if len(l.strip())]

setup(
    name="gutenberg2zim",
    version=VERSION,
    description=__doc__,
    long_description=readme,
    author="Kiwix",
    author_email="reg@kiwix.org",
    url="http://github.com/openzim/gutenberg",
    keywords="gutenberg zim kiwix openzim offline",
    license="GPL-3.0",
    packages=find_packages("."),
    zip_safe=False,
    platforms="any",
    include_package_data=True,
    data_files=["pypi-readme.rst", "LICENSE", "requirements.pip"],
    package_dir={"gutenberg": "gutenberg"},
    install_requires=requirements,
    scripts=["gutenberg2zim"],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
    ],
)
