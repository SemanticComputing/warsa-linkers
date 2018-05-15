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

from .utils import query_sparql

log = logging.getLogger(__name__)

CRM = Namespace('http://www.cidoc-crm.org/cidoc-crm/')

DATE_FORMAT = '%Y-%m-%d'


def link_persons(graph, endpoint, cas_data):
    """
    Link military persons in graph.

    :param graph: Data in RDFLib Graph object
    :param endpoint: Endpoint to query persons from
    :param cas_data:
    :return: RDFLib Graph with updated links
    """

    data_fields = [
        {'field': 'given', 'type': 'String'},
        {'field': 'family', 'type': 'String'},
        # Birth place is linked, can have multiple values
        {'field': 'birth_place', 'type': 'Custom', 'comparator': intersection_comparator, 'has missing': True},
        {'field': 'birth_begin', 'type': 'DateTime', 'has missing': True, 'fuzzy': False},
        {'field': 'birth_end', 'type': 'DateTime', 'has missing': True, 'fuzzy': False},
        {'field': 'death_begin', 'type': 'DateTime', 'has missing': True, 'fuzzy': False},
        {'field': 'death_end', 'type': 'DateTime', 'has missing': True, 'fuzzy': False},
        {'field': 'activity_end', 'type': 'Custom', 'comparator': activity_comparator, 'has missing': True},
        {'field': 'rank', 'type': 'Exact', 'has missing': True},
        {'field': 'rank_level', 'type': 'Price', 'has missing': True},
    ]

    log.info('Got {} casualty persons'.format(len(cas_data)))

    per_data = _generate_persons_dict(endpoint)
    log.info('Got {} WarSampo persons'.format(len(per_data)))

    cas_data, num_links = get_person_links(cas_data, per_data)

    log.info('Got {} person links as training data'.format(num_links))

    link_graph = Graph()
    if num_links:
        linker = RecordLink(data_fields)
        linker.sample(cas_data, per_data, sample_size=len(cas_data) * 2)
        linker.markPairs(trainingDataLink(cas_data, per_data, common_key='person'))
        linker.train()

        with open('output/training_data.json', 'w') as fp:
            linker.writeTraining(fp)

        threshold = linker.threshold(cas_data, per_data, 0.5)  # Set desired recall / precision importance ratio
        links = linker.match(cas_data, per_data, threshold=threshold)
        log.info('Found {} person links'.format(len(links)))

        for link in links:
            cas = link[0][0]
            per = link[0][1]
            log.debug('Found person link: {}  <-->  {} (confidence: {})'.format(cas, per, link[1]))
            link_graph.add((URIRef(cas), CRM.P70_documents, URIRef(per)))

        log.info('Got weights: {}'.format(linker.classifier.weights))

    return link_graph


def _generate_persons_dict(endpoint):
    """
    Generate a persons dict from person instances
    """

    def get_person_query():
        with open('SPARQL/warsa_persons.sparql') as f:
            return f.read()

    sparql = SPARQLWrapper(endpoint)
    sparql.method = 'POST'
    sparql.setQuery(get_person_query())
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


def get_date_value(date_literal):
    """
    Get date value from literal
    >>> get_date_value('1945-02-01')
    datetime.date(1945, 2, 1)
    >>> get_date_value(None)
    >>> get_date_value('1945-02-31')
    >>> get_date_value('1945-02-XX')
    """
    if date_literal:
        try:
            return datetime.strptime(str(date_literal), DATE_FORMAT).isoformat()
        except ValueError:
            log.warning('Unable to parse date {}'.format(date_literal))


def get_person_links(casualties: dict, persons: dict, links_json_file='input/person_links.json'):
    """
    Read person links from a JSON file generated with generate_training_data.sh
    """
    with open(links_json_file, 'r') as fp:
        links = json.load(fp)['results']['bindings']

    num_links = 0

    for link in links:
        cas = link['doc']['value']
        per = link['person']['value']
        if cas in casualties and per in persons:
            casualties[cas].update({'person': per})
            num_links += 1
        else:
            log.warning('Could not find linked person: {} - {}'.format(cas, per))

    return casualties, num_links


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
    """
    if cas_death and per_activity:
        if cas_death >= per_activity:
            return 0
        try:
            if (datetime.strptime(cas_death, DATE_FORMAT) + timedelta(days=30)) < datetime.strptime(per_activity,
                                                                                                    DATE_FORMAT):
                return 1
        except ValueError:
            pass

