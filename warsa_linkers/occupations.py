#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Link occupation strings to WarSampo occupation ontology"""
import argparse
import logging
import re

import time

import sys
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, RDF
from rdflib.util import guess_format

log = logging.getLogger(__name__)


def _query_sparql(sparql_obj):
    """
    Query SPARQL with retry functionality

    :type sparql_obj: SPARQLWrapper
    :return: SPARQL query results
    """
    results = None
    retry = 0
    while not results:
        try:
            results = sparql_obj.query().convert()
        except ValueError:
            if retry < 10:
                log.error('Malformed result for query {p_uri}, retrying in 1 second...'.format(
                    p_uri=sparql_obj.queryString))
                retry += 1
                time.sleep(1)
            else:
                raise
    log.debug('Got results {res} for query {q}'.format(res=results, q=sparql_obj.queryString))
    return results


def link_occupations(graph, endpoint, source_property: URIRef, target_property: URIRef, resource_type: URIRef):
    """
    Link occupations in graph.

    :param graph: Data in RDFLib Graph object
    :param endpoint: SPARQL endpoint
    :return: RDFLib Graph with updated links
    """

    escape_regex = r'[\[\]\\/\&|!(){}^"~*?:+]'
    escape = re.compile(escape_regex)

    def preprocess(literal):
        literal = str(literal).strip()

        if literal == '-':
            return ''

        values = '" "'.join([escape.sub(r'\\\\\g<0>', s.strip()) for s in literal.split(sep='/') if s])

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

    sparql = SPARQLWrapper(endpoint)
    sparql.method = 'POST'
    sparql.setQuery(query.format(values='" "'.join(literals)))
    sparql.setReturnFormat(JSON)
    results = _query_sparql(sparql)

    links = Graph()
    uris = {}
    for res in results['results']['bindings']:
        uris[res['value']['value']] = res['id']['value']

    for person in graph[:RDF.type:resource_type]:
        literals = graph.objects(person, source_property)
        for literal in literals:
            literal = str(literal)
            if literal in uris:
                links.add((person, target_property, URIRef(uris[literal])))

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
