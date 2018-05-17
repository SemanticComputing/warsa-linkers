#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
import datetime
import pprint
import unittest
from unittest import mock

from rdflib import URIRef, Graph, Literal, RDF

from .person_record_linkage import _generate_persons_dict
from .occupations import link_occupations


class OccupationTest(unittest.TestCase):
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

        with mock.patch('warsa_linkers.occupations.query_sparql',
                        side_effect=lambda x: self.OCCUPATION_LINK_SPARQL_RESULTS):
            results = link_occupations(graph, '', source_prop, target_prop, ptype)

        self.assertEqual(3, len(results))

        workman = URIRef('http://ldf.fi/warsa/occupations/tyomies')

        self.assertIsNotNone(results.triples((p1, target_prop, workman)))
        self.assertEqual(2, len(list(results.triples((p2, target_prop, None)))))


class PersonRecordLinkageTest(unittest.TestCase):
    WARSA_PERSONS_SPARQL_RESULTS = {
        "head": {
            "vars": ["person", "given", "family", "birth_begin", "birth_end", "birth_place", "death_begin", "death_end",
                     "death_place", "rank", "rank_level", "activitity_end"]
        },
        "results": {
            "bindings": [
                {
                    "person": {"type": "uri", "value": "http://ldf.fi/warsa/actors/person_5513"},
                    "given": {"type": "literal", "value": "J."},
                    "family": {"type": "literal", "value": "Nurmi"},
                    "rank": {"type": "uri", "value": "http://ldf.fi/warsa/actors/ranks/Vaenrikki"},
                    "rank_level": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                                   "value": "9"}
                },
                {
                    "person": {"type": "uri", "value": "http://ldf.fi/warsa/actors/person_4399"},
                    "given": {"type": "literal", "xml:lang": "fi", "value": "Armas Pekka"},
                    "family": {"type": "literal", "value": "Herka Ent.Hägglund"},
                    "birth_begin": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#date",
                                    "value": "1896-06-18"},
                    "birth_end": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#date",
                                  "value": "1896-06-18"},
                    "birth_place": {"type": "uri", "value": "http://ldf.fi/warsa/places/municipalities/m_place_223"},
                    "death_begin": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#date",
                                    "value": "1962-05-04"},
                    "death_end": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#date",
                                  "value": "1962-05-04"},
                    "rank": {"type": "uri", "value": "http://ldf.fi/warsa/actors/ranks/Eversti"},
                    "rank_level": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                                   "value": "15"},
                    "activity_end": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#date",
                                     "value": "1940-01-01"}
                },
                {
                    "person": {"type": "uri", "value": "http://ldf.fi/warsa/actors/person_3380"},
                    "given": {"type": "literal", "value": "Niilo Johannes"},
                    "family": {"type": "literal", "value": "Lahdenperä"},
                    "birth_begin": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#date",
                                    "value": "1896-10-05"},
                    "birth_end": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#date",
                                  "value": "1896-10-05"},
                    "birth_place": {"type": "uri", "value": "http://ldf.fi/warsa/places/municipalities/m_place_47"},
                    "death_begin": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#date",
                                    "value": "1944-11-19"},
                    "death_end": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#date",
                                  "value": "1944-11-19"},
                    "death_place": {"type": "uri", "value": "http://ldf.fi/warsa/places/municipalities/m_place_302"},
                    "rank": {"type": "uri", "value": "http://ldf.fi/warsa/actors/ranks/Kapteeni"},
                    "rank_level": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                                   "value": "12"},
                    "activity_end": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#date",
                                     "value": "1941-01-01"}
                },
                {
                    "person": {"type": "uri", "value": "http://ldf.fi/warsa/actors/person_1270"},
                    "given": {"type": "literal", "value": "Lennart"},
                    "family": {"type": "literal", "value": "Holmberg"},
                    "rank": {"type": "uri", "value": "http://ldf.fi/warsa/actors/ranks/Alikersantti"},
                    "rank_level": {"type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                                   "value": "3"}
                },
                {
                    "person": {"type": "uri", "value": "http://ldf.fi/warsa/actors/person_1407"},
                    "given": {"type": "literal", "value": "Aili Irja"},
                    "family": {"type": "literal", "value": "Lamppu"}
                },
            ]
        }
    }

    EXPECTED_RESULTS = {
        'http://ldf.fi/warsa/actors/person_1270': {
            'activity_end': None,
            'birth_begin': None,
            'birth_end': None,
            'birth_place': None,
            'death_begin': None,
            'death_end': None,
            'family': 'Holmberg',
            'given': 'Lennart',
            'person': 'http://ldf.fi/warsa/actors/person_1270',
            'rank': 'http://ldf.fi/warsa/actors/ranks/Alikersantti',
            'rank_level': 3
        },
        'http://ldf.fi/warsa/actors/person_1407': {
            'activity_end': None,
            'birth_begin': None,
            'birth_end': None,
            'birth_place': None,
            'death_begin': None,
            'death_end': None,
            'family': 'Lamppu',
            'given': 'Aili Irja',
            'person': 'http://ldf.fi/warsa/actors/person_1407',
            'rank': None,
            'rank_level': None
        },
        'http://ldf.fi/warsa/actors/person_3380': {
            'activity_end': datetime.date(1941, 1, 1),
            'birth_begin': datetime.date(1896, 10, 5),
            'birth_end': datetime.date(1896, 10, 5),
            'birth_place': ['http://ldf.fi/warsa/places/municipalities/m_place_47'],
            'death_begin': datetime.date(1944, 11, 19),
            'death_end': datetime.date(1944, 11, 19),
            'family': 'Lahdenperä',
            'given': 'Niilo '
                     'Johannes',
            'person': 'http://ldf.fi/warsa/actors/person_3380',
            'rank': 'http://ldf.fi/warsa/actors/ranks/Kapteeni',
            'rank_level': 12
        },
        'http://ldf.fi/warsa/actors/person_4399': {
            'activity_end': datetime.date(1940, 1, 1),
            'birth_begin': datetime.date(1896, 6, 18),
            'birth_end': datetime.date(1896, 6, 18),
            'birth_place': ['http://ldf.fi/warsa/places/municipalities/m_place_223'],
            'death_begin': datetime.date(1962, 5, 4),
            'death_end': datetime.date(1962, 5, 4),
            'family': 'Herka Hägglund',
            'given': 'Armas Pekka',
            'person': 'http://ldf.fi/warsa/actors/person_4399',
            'rank': 'http://ldf.fi/warsa/actors/ranks/Eversti',
            'rank_level': 15
        },
        'http://ldf.fi/warsa/actors/person_5513': {
            'activity_end': None,
            'birth_begin': None,
            'birth_end': None,
            'birth_place': None,
            'death_begin': None,
            'death_end': None,
            'family': 'Nurmi',
            'given': 'J.',
            'person': 'http://ldf.fi/warsa/actors/person_5513',
            'rank': 'http://ldf.fi/warsa/actors/ranks/Vaenrikki',
            'rank_level': 9
        }
    }

    def test_generate_persons_dict(self):
        with mock.patch('warsa_linkers.person_record_linkage.query_sparql',
                        side_effect=lambda x: self.WARSA_PERSONS_SPARQL_RESULTS):
            results = _generate_persons_dict('http://sparql')

            self.assertEqual(results, self.EXPECTED_RESULTS, pprint.pformat(results))


if __name__ == '__main__':
    unittest.main()
