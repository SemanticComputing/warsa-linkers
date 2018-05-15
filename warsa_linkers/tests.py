#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-

import unittest
from unittest import mock

from rdflib import URIRef, Graph, Literal, RDF

from .occupations import link_occupations


OCCUPATION_LINK_SPARQL_RESULTS = {
    "head": {
        "vars": ["value", "id"]
    },
    "results": {
        "bindings": [
            {
                "value": {"type": "literal", "value": "työmies"},
                "id": {"type": "uri", "value": "http://ldf.fi/warsa/occupations/tyomies"}
            },
            {
                "value": {"type": "literal", "value": "silinterimies"},
                "id": {"type": "uri", "value": "http://ldf.fi/warsa/occupations/silinterimies"}
            },
            {
                "value": {"type": "literal", "value": "juuston suolaaja"},
                "id": {"type": "uri", "value": "http://ldf.fi/warsa/occupations/juustonsuolaaja"}
            }
        ]
    }
}


class OccupationTest(unittest.TestCase):
    def test_link_occupations(self):
        source_prop = URIRef('http://occupation')
        target_prop = URIRef('http://occupation_link')
        p1 = URIRef('http://person/1')
        p2 = URIRef('http://person/2')
        p3 = URIRef('http://person/3')
        ptype = URIRef('http://tyomies')

        graph = Graph()
        graph.add((p1, source_prop, Literal('silinterimies', lang='fi')))
        graph.add((p2, source_prop, Literal('työmies')))
        graph.add((p2, source_prop, Literal('juuston suolaaja')))
        graph.add((p3, source_prop, Literal('kakkaaja')))

        for p in [p1, p2, p3]:
            graph.add((p, RDF.type, ptype))

        with mock.patch('warsa_linkers.occupations.query_sparql', side_effect=lambda x: OCCUPATION_LINK_SPARQL_RESULTS):
            results = link_occupations(graph, '', source_prop, target_prop, ptype)

        self.assertEqual(3, len(results))

        workman = URIRef('http://ldf.fi/warsa/occupations/tyomies')

        self.assertIsNotNone(results.triples((p1, target_prop, workman)))
        self.assertEqual(2, len(list(results.triples((p2, target_prop, None)))))


if __name__ == '__main__':
    unittest.main()