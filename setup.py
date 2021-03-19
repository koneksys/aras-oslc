#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

# imports
from io import open
from os.path import exists
from datetime import datetime as dt
from setuptools import find_packages as fp, setup

vfile = "VERSION"
cfile = "COMMITNO"
dtfmt = "%Y%m%d%H%M%S"


""" define inline read file """


def read(n):
    return open(n, "r").read().strip()


""" read VERSION file """
ver = read(vfile)

""" then append version with the commit number or timestamp """
if exists(cfile):
    ver += "." + read(cfile)
else:
    ver += ".dev" + dt.now().strftime(dtfmt)

print(f"VERSION {ver}")

""" execute setup """
setup(
    name="aras-oslc-api",
    description="OSLC API implementation to expose Aras ItemTypes in RDF representation.",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    url="https://aras.koneksys.com",
    author="Fabio",
    author_email="fabio.ribeiro@koneksys.com",
    keywords=['aras', 'plm', 'oslc', 'rdf', 'json-ld'],
    packages=fp(exclude=["*.tests", "*.tests.*", "tests.*"]),
    install_requires=[
        "python-dotenv",
        "RDFLib",
        "RDFLib-JSONLD",
        "Flask",
        "Flask-RESTx",
        "Flask-Login",
        "Flask-SQLAlchemy",
        "flask_cors",
        "requests",
        "blinker",
    ],
    extras_require={},
    python_requires=">=3.6.0",
    include_package_data=True,
    license=None,
    version=ver,
)
