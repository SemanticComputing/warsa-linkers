#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Link occupation strings to WarSampo occupation ontology"""
import argparse
import logging
import operator
import re

import sys

import requests
from collections import defaultdict
from rdflib import Graph, URIRef, RDF
from rdflib.util import guess_format

log = logging.getLogger(__name__)


def link_occupations(graph, endpoint, source_property: URIRef, target_property: URIRef, resource_type: URIRef, sep='/'):
    """
    Link occupations in graph.

    :param graph: Data in RDFLib Graph object
    :param endpoint: SPARQL endpoint
    :param source_property: Source property for linking
    :param target_property: Property to use for writing found links
    :param resource_type: Class of resources to be linked
    :return: RDFLib Graph with updated links
    """

    escape_regex = r'[\[\]\\/\&|!(){}^"~*?:+]'
    escape = re.compile(escape_regex)

    valuemap = {
        'aut.kulj.': 'autonkuljettaja',
        'maanvilj.tytär': 'maanviljelijän tytär',
        'mv.': 'maanviljelijä',
        'mv.p': 'maanviljelijän poika',
        'mv.p.': 'maanviljelijän poika',
        'mv.pka': 'maanviljelijän poika',
        'mv. pka': 'maanviljelijän poika',
        'myym.hoit.': 'myymälän hoitaja',
        'kalast.': 'kalastaja',
        'koulul.': 'koululainen',
        'taloll.pka': 'talollisen poika',
        'talollisen pka': 'talollisen poika',
        'tal.pka': 'talollisen poika',
        'taloll.': 'talollinen',
        'teurast.': 'teurastaja',
        'tilall.pka': 'tilallisen poika',
        'tilall. pka': 'tilallisen poika',
        'teht.työm.': 'tehdastyöläinen',
        'opisk.': 'opiskelija',
        'poliisikonst': 'poliisikonstaapeli',
        'poliisikonst.': 'poliisikonstaapeli',
        'rak.työm.': 'rakennustyöläinen',
        'viilankarkais.': 'viilankarkaisija',
    }

    subs = [
        (r'(.+)(\.| +)(pka)', r'\1 poika'),
        (r'(.+)(m\.)$', r'\1mies'),
        (r'(.+)(apul\.)', r'\1apulainen'),
        (r'(.+)(harj\.)$', r'\1harjoittelija'),
        (r'(.+)(hoit\.)', r'\1hoitaja'),
        (r'(.+)(joht\.)', r'\1johtaja'),
        (r'(.+)(mest\.)', r'\1mestari'),
        (r'(.+)(työntek\.)', r'\1työntekijä'),
        (r'(.+)(op\.)', r'\1opettaja'),
        (r'(.+)(opett\.)', r'\1opettaja'),
        (r'(.+)(ins\.)', r'\1insinööri'),
        (r'(...+)(s\.)$', r'\1seppä'),

        (r'(.*)(asent\.)', r'\1asentaja'),
        (r'(.*)(kaupp\.)', r'\1kauppias'),
        (r'(.*)(kulj\.)', r'\1kuljettaja'),
        (r'(.*)(kuljett\.)', r'\1kuljettaja'),
        (r'(.*)(lämmitt\.)', r'\1lämmittäjä'),
        (r'(.*)(teht\. *)', r'\1tehtaan '),
        (r'(.*)(tilall\.)', r'\1tilallinen'),
        (r'(.*)(pientil\.) (.+)', r'\1pientilallisen \3'),
        (r'(.*)(työl\.)', r'\1työläinen'),
        (r'(.*)(työnj\.)', r'\1työnjohtaja'),

        (r'^(palstatil\. *)(.+)', r'palstatilallisen \2'),
        (r'^(taloll\. *)(.+)', r'talollisen \2'),
    ]

    def harmonize(literal):
        literal = str(literal).strip()

        if literal == '-':
            return ''

        processed = []
        for s in literal.split(sep=sep):
            if not s:
                continue

            s = s.strip()
            if s in valuemap:
                value = valuemap[s]
            else:
                value = s
                for sub in subs:
                    value = re.sub(sub[0], sub[1], value)

            if s != value:
                processed.append(value)
                log.debug('Processed occupation {old} into {new}'.format(old=s, new=value))
            else:
                processed.append(s)

        return processed

    def preprocess(literal):
        literal = str(literal).strip()

        values = '" "'.join([escape.sub(r'\\\\\g<0>', s) for s in harmonize(literal)])

        return values

    query = """
        PREFIX text: <http://jena.apache.org/text#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT ?value ?id {{
            GRAPH <http://ldf.fi/warsa/occupations> {{
                VALUES ?value {{ "{values}" }} .
                ?id text:query ?value .
                ?id a <http://ldf.fi/schema/bioc/Occupation> .
                ?id skos:prefLabel|skos:altLabel ?label .
                FILTER(LCASE(?value) = LCASE(str(?label)))
            }}
         }}
    """

    literals = set(map(preprocess, graph.objects(None, source_property)))

    log.info('Got {n} occupations for linking'.format(n=len(literals)))
    results = requests.post(endpoint, {'query': query.format(values='" "'.join(literals))}).json()

    links = Graph()
    uris = {}
    for res in results['results']['bindings']:
        uris[res['value']['value']] = res['id']['value']

    unlinked_occupations = defaultdict(int)

    for person in graph[:RDF.type:resource_type]:
        literals = graph.objects(person, source_property)
        for literal in literals:
            harmonized = harmonize(literal)
            for occupation in harmonized:
                if occupation in uris:
                    links.add((person, target_property, URIRef(uris[occupation])))
                else:
                    unlinked_occupations[occupation] += 1

    for literal, count in sorted(unlinked_occupations.items(), key=operator.itemgetter(1, 0), reverse=True):
        log.warning('No URI found for occupation: {o}  ({c})'.format(o=literal, c=count))

    return links


if __name__ == '__main__':
    if sys.argv[1] == 'test':
        import doctest
        doctest.testmod()
        exit()

    argparser = argparse.ArgumentParser(description="Occupation linking", fromfile_prefix_chars='@')

    argparser.add_argument("input", help="Input RDF file")
    argparser.add_argument("output", help="Output file location")
    argparser.add_argument("source_prop", help="Source property")
    argparser.add_argument("target_prop", help="Target property")
    argparser.add_argument("res_class", help="Resource class")
    argparser.add_argument("endpoint", help="SPARQL Endpoint")

    args = argparser.parse_args()

    input_graph = Graph()
    input_graph.parse(args.input, format=guess_format(args.input))

    links = link_occupations(input_graph,
                             args.endpoint,
                             URIRef(args.source_prop),
                             URIRef(args.target_prop),
                             URIRef(args.res_class))

    links.serialize(args.output, format=guess_format(args.output))
