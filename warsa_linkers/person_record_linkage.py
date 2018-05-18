#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Link person records to WarSampo persons"""
import logging
import re
import json

from SPARQLWrapper import SPARQLWrapper, JSON
from collections import defaultdict

from datetime import datetime, timedelta
from dedupe import RecordLink, trainingDataLink
from rdflib import Graph, URIRef, Namespace

from warsa_linkers.utils import query_sparql

log = logging.getLogger(__name__)

CRM = Namespace('http://www.cidoc-crm.org/cidoc-crm/')

INPUT_DATE_FORMAT = '%Y-%m-%d'
ISO_FORMAT = '%Y-%m-%d'

QUERY_WARSA_PERSONS = '''
PREFIX wsch: <http://ldf.fi/schema/warsa/>
PREFIX wsa: <http://ldf.fi/schema/warsa/actors/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX text: <http://jena.apache.org/text#>
SELECT ?person ?given ?family ?birth_begin ?birth_end ?birth_place ?death_begin ?death_end ?death_place ?rank (SAMPLE(?rank_lvl) AS ?rank_level) (MAX(?event_begin) as ?activity_end)
WHERE {
      ?person a wsch:Person .
      ?person foaf:firstName ?given .
      ?person foaf:familyName ?family .
  OPTIONAL {
    ?person ^crm:P98_brought_into_life ?birth .
    ?birth crm:P4_has_time-span [
        crm:P82a_begin_of_the_begin ?birth_begin ;
        crm:P82b_end_of_the_end ?birth_end ;
        ]
    OPTIONAL { ?birth crm:P7_took_place_at ?birth_place . }
  }
  OPTIONAL {
    ?person ^crm:P100_was_death_of ?death .
    ?death crm:P4_has_time-span [
        crm:P82a_begin_of_the_begin ?death_begin ;
        crm:P82b_end_of_the_end ?death_end ;
        ]
    OPTIONAL { ?death crm:P7_took_place_at ?death_place . }
  }
  OPTIONAL {
    ?promo crm:P11_had_participant ?person .
    ?promo a wsch:Promotion .
    ?promo wsa:hasRank ?rank .
    ?rank wsa:level ?rank_lvl .
    ?person ^crm:P11_had_participant/wsa:hasRank/wsa:level ?rank_level2 .
  }
  OPTIONAL { ?person ^crm:P11_had_participant/crm:P4_has_time-span/crm:P82a_begin_of_the_begin ?event_begin }
}
GROUP BY ?person ?given ?family ?birth_begin ?birth_end ?birth_place ?death_begin ?death_end ?death_place ?rank
HAVING(MAX(COALESCE(?rank_lvl, 1)) >= MAX(COALESCE(?rank_level2, 1)))
'''


def link_persons(graph, endpoint, doc_data, data_fields, links_json_file, sample_size=200000, threshold_ratio=0.5):
    """
    Link document records of persons to WarSampo person instances.

    :param graph: Data in RDFLib Graph object
    :param endpoint: Endpoint to query persons from
    :param doc_data: Dataset of person documents
    :param data_fields: Data field specifications for linking
    :param links_json_file: Known person links file
    :param sample_size: Sample size for training
    :param threshold_ratio: Desired recall / precision importance ratio
    :return: RDFLib Graph with updated links
    """
    log.info('Got {} document records'.format(len(doc_data)))

    per_data = _generate_persons_dict(endpoint)
    log.info('Got {} WarSampo persons'.format(len(per_data)))

    doc_data, num_links = get_person_links(doc_data, per_data, links_json_file)

    log.info('Got {} person links as training data'.format(num_links))

    link_graph = Graph()
    if num_links:
        linker = RecordLink(data_fields)
        linker.sample(doc_data, per_data, sample_size=sample_size)
        linker.markPairs(trainingDataLink(doc_data, per_data, common_key='person'))
        linker.train()

        with open('output/training_data.json', 'w') as fp:
            linker.writeTraining(fp)

        threshold = linker.threshold(doc_data, per_data, threshold_ratio)
        links = linker.match(doc_data, per_data, threshold=threshold)
        log.info('Found {} person links'.format(len(links)))

        for link in links:
            cas = link[0][0]
            per = link[0][1]
            log.info('Found person link: {}  <-->  {} (confidence: {})'.format(cas, per, link[1]))
            link_graph.add((URIRef(cas), CRM.P70_documents, URIRef(per)))

        log.info('Got weights: {}'.format(linker.classifier.weights))

    return link_graph


def _generate_persons_dict(endpoint):
    """
    Generate a persons dict from person instances
    """

    sparql = SPARQLWrapper(endpoint)
    sparql.method = 'POST'
    sparql.setQuery(QUERY_WARSA_PERSONS)
    sparql.setReturnFormat(JSON)
    results = query_sparql(sparql)

    persons = defaultdict(dict)
    for person_row in results['results']['bindings']:
        person = person_row['person']['value']
        given = person_row['given']['value']
        family = person_row['family']['value']
        rank = person_row.get('rank', {}).get('value')
        rank_level = person_row.get('rank_level', {}).get('value')
        birth_place = person_row.get('birth_place', {}).get('value')
        birth_begin = person_row.get('birth_begin', {}).get('value')
        birth_end = person_row.get('birth_end', {}).get('value')
        death_begin = person_row.get('death_begin', {}).get('value')
        death_end = person_row.get('death_end', {}).get('value')
        activity_end = person_row.get('activity_end', {}).get('value')

        person_dict = {
            'person': person,
            'given': given,
            'family': re.sub(r'\s+E(?:nt)?\.\s*', ' ', family),
            'rank': rank,
            'rank_level': int(rank_level) if rank_level else None,
            'birth_place': [birth_place] if birth_place else None,
            'birth_begin': get_date_value(birth_begin),
            'birth_end': get_date_value(birth_end),
            'death_begin': get_date_value(death_begin),
            'death_end': get_date_value(death_end),
            'activity_end': get_date_value(activity_end),
        }
        persons[person] = person_dict

        if person_dict['rank'] is not None:
            log.debug('WarSampo person: {}'.format(person_dict))

    return persons


def get_date_value(date_str, date_format=INPUT_DATE_FORMAT):
    """
    Validate date values and return them in the format expected by dedupe (string).

    >>> get_date_value('1945-02-01')
    '1945-02-01'
    >>> get_date_value(None)
    >>> get_date_value('1945-02-31')
    >>> get_date_value('1945-02-XX')
    """
    if date_str:
        try:
            return datetime.strptime(str(date_str), date_format).date().isoformat()
        except ValueError:
            log.warning('Unable to parse date {}'.format(date_str))


def get_person_links(documents: dict, persons: dict, links_json_file):
    """
    Read person links from a JSON file
    """
    with open(links_json_file, 'r') as fp:
        links = json.load(fp)['results']['bindings']

    num_links = 0

    for link in links:
        doc = link['doc']['value']
        per = link['person']['value']
        if doc in documents and per in persons:
            documents[doc].update({'person': per})
            num_links += 1
        else:
            log.warning('Could not find linked person: {} - {}'.format(doc, per))

    return documents, num_links


def intersection_comparator(field_1, field_2):
    if field_1 and field_2:
        if set(field_1) & set(field_2):
            return 0
        else:
            return 1


def activity_comparator(cas_death, per_activity):
    """
    Compare death date with activity time from WarSampo events
    >>> activity_comparator('1944-04-02', '1944-04-02')
    0
    >>> activity_comparator('1944-04-12', '1944-04-02')
    0
    >>> activity_comparator('1944-04-12', '1944-05-01')
    >>> activity_comparator('1941-11-24', '1944-04-02')
    1
    >>> activity_comparator('1944-04-12', None)
    >>> activity_comparator('1944-07-12', '1944-05-91')
    Traceback (most recent call last):
     ...
    ValueError: unconverted data remains: 1
    """
    if cas_death and per_activity:
        death = datetime.strptime(cas_death, ISO_FORMAT)
        activity = datetime.strptime(per_activity, ISO_FORMAT)

        if death >= activity:
            return 0
        if death + timedelta(days=30) < activity:
            return 1  # Was active after death

