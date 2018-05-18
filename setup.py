import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="warsa_linkers",
    version="0.5.0",
    author="Erkki Heino, Mikko Koho",
    description="WarSampo entity linking",
    license="MIT",
    keywords="rdf",
    url="https://github.com/SemanticComputing/warsa-linkers",
    long_description=read('README.md'),
    packages=['warsa_linkers'],
    package_data={'': ['*.sparql']},
    install_requires=[
        'rdflib >= 4.2.0',
        'requests >= 2.7.0',
        'roman',
        'SPARQLWrapper',
        'dedupe',
    ],
)
