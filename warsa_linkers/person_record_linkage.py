#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Link person records to WarSampo persons"""
import logging
import re
import json
import requests

from collections import defaultdict

from datetime import datetime, timedelta
from dedupe import RecordLink, trainingDataLink, StaticRecordLink
from rdflib import Graph, URIRef, Namespace

log = logging.getLogger(__name__)

CRM = Namespace('http://www.cidoc-crm.org/cidoc-crm/')

INPUT_DATE_FORMAT = '%Y-%m-%d'
ISO_FORMAT = '%Y-%m-%d'

# TODO: Handle SAMPLEd duplicate values better

QUERY_WARSA_PERSONS = '''
PREFIX wsch: <http://ldf.fi/schema/warsa/>
PREFIX wsa: <http://ldf.fi/schema/warsa/actors/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX text: <http://jena.apache.org/text#>
PREFIX biocrm: <http://ldf.fi/schema/bioc/>
SELECT ?person (SAMPLE(?given_) as ?given) (SAMPLE(?family_) as ?family) (SAMPLE(?birth_begin_) as ?birth_begin) (SAMPLE(?birth_end_) as ?birth_end) 
    (SAMPLE(?birth_place_) as ?birth_place) (SAMPLE(?death_begin_) as ?death_begin) (SAMPLE(?death_end_) as ?death_end) (SAMPLE(?death_place_) as ?death_place)
    (GROUP_CONCAT(DISTINCT ?rank; separator='|') as ?ranks)
    (SAMPLE(?rank_lvl) AS ?rank_level) 
    (MAX(?event_begin) as ?activity_end)
    (GROUP_CONCAT(DISTINCT ?unit; separator='|') as ?units) 
    (GROUP_CONCAT(DISTINCT ?occupation; separator='|') as ?occupations) 
WHERE {
  ?person a wsch:Person .
  ?person foaf:firstName ?given_ .
  ?person foaf:familyName ?family_ .
  OPTIONAL {
    ?person ^crm:P98_brought_into_life ?birth .
    ?birth crm:P4_has_time-span [
        crm:P82a_begin_of_the_begin ?birth_begin_ ;
        crm:P82b_end_of_the_end ?birth_end_ ;
        ]
    OPTIONAL { ?birth crm:P7_took_place_at ?birth_place_ . }
  }
  OPTIONAL {
    ?person ^crm:P100_was_death_of ?death .
    ?death crm:P4_has_time-span [
        crm:P82a_begin_of_the_begin ?death_begin_ ;
        crm:P82b_end_of_the_end ?death_end_ ;
        ]
    OPTIONAL { ?death crm:P7_took_place_at ?death_place_ . }
  }
  OPTIONAL {
    ?promo crm:P11_had_participant ?person .
    ?promo a wsch:Promotion .
    ?promo wsa:hasRank ?rank .
    ?rank wsa:level ?rank_lvl .
    ?person ^crm:P11_had_participant/wsa:hasRank/wsa:level ?rank_level2 .
  }
  OPTIONAL { ?person ^crm:P11_had_participant/crm:P4_has_time-span/crm:P82a_begin_of_the_begin ?event_begin }
  OPTIONAL { ?person ^crm:P143_joined/crm:P144_joined_with ?unit }
  OPTIONAL { ?person biocrm:has_occupation ?occupation }
}
GROUP BY ?person 
HAVING(MAX(COALESCE(?rank_lvl, 1)) >= MAX(COALESCE(?rank_level2, 1)))
'''


def init_linker(data_fields, training_data_file, training_settings_file, doc_data, per_data, sample_size, training_size):
    if training_settings_file:
        try:
            with open(training_settings_file, 'rb') as f:
                linker = StaticRecordLink(f)
                log.info('Read settings from {}'.format(training_settings_file))
                return linker
        except FileNotFoundError:
            pass

    linker = RecordLink(data_fields)

    if training_data_file:
        try:
            with open(training_data_file) as f:
                linker.readTraining(f)
                log.info('Read training data from {}'.format(training_data_file))
        except FileNotFoundError:
            pass

    log.info('Generating training data')
    linker.sample(doc_data, per_data, sample_size=sample_size)
    linker.markPairs(trainingDataLink(doc_data, per_data, common_key='person', training_size=training_size))
    linker.train()

    if training_data_file:
        log.info('Writing training data to {}'.format(training_data_file))
        with open(training_data_file, 'w+') as fp:
            linker.writeTraining(fp)

    if training_settings_file:
        log.info('Writing settings data to {}'.format(training_settings_file))
        with open(training_settings_file, 'wb+') as fp:
            linker.writeSettings(fp)

    return linker


def _finalize_links(link_graph: Graph, training_links: list):
    """
    Add all training links to the output, as some can occasionally be missing.
    """
    for link in training_links:
        doc = link[0]
        per = link[1]
        link_graph.add((URIRef(doc), CRM.P70_documents, URIRef(per)))

    return link_graph


def read_person_links(json_file: str):
    """
    Read person links to use as training data.
    :param json_file: JSON file with person-document pairs formatted as a SPARQL JSON result.
    :return: List of person-document pair tuples
    """
    with open(json_file, 'r') as fp:
        links = json.load(fp)['results']['bindings']

    link_tuples = []

    for link in links:
        doc = link['doc']['value']
        per = link['person']['value']
        link_tuples.append((doc, per))

    log.info('Got {} person links as training data'.format(len(links)))

    return link_tuples


def link_persons(endpoint, doc_data, data_fields, training_links,
                 sample_size=200000,
                 training_size=50000,
                 threshold_ratio=0.5,
                 training_data_file=None,
                 training_settings_file=None):
    """
    Link document records of persons to WarSampo person instances.

    :param endpoint: Endpoint to query persons from
    :param doc_data: Dataset of person documents
    :param data_fields: Data field specifications for linking
    :param training_links: Known person links file
    :param sample_size: Size of the sample to draw for active learning
    :param training_size: limit of number of training examples for consumption by the ActiveLearning markPairs method
    :param threshold_ratio: Desired recall / precision importance (between 0 and 1)
    :param training_data_file:
    :param training_settings_file:
    :return: RDFLib Graph with updated links
    """
    log.info('Got {} document records'.format(len(doc_data)))

    per_data = _generate_persons_dict(endpoint)
    log.info('Got {} WarSampo persons'.format(len(per_data)))

    doc_data = get_person_links(doc_data, per_data, training_links)

    link_graph = Graph()

    linker = init_linker(data_fields, training_data_file, training_settings_file, doc_data, per_data,
                         sample_size, training_size)

    # threshold_ratio = linker.threshold(doc_data, per_data, threshold_ratio)
    links = linker.match(doc_data, per_data, threshold=threshold_ratio)

    for link in links:
        doc = link[0][0]
        per = link[0][1]
        link_graph.add((URIRef(doc), CRM.P70_documents, URIRef(per)))

        log.info('Found person link: {}  <-->  {} (confidence: {})'.format(doc, per, link[1]))
        log.debug('\nLinked document: {}\n'.format(dict(doc_data[doc])))
        log.debug('Linked Warsa person: {}\n'.format(dict(per_data[per])))

    log.info('Got weights: {}'.format(linker.classifier.weights))
    log.info('Found {} person links'.format(len(links)))

    return _finalize_links(link_graph, training_links)


def _sanitize_family_name(name: str):
    """
    :param name:
    :return:

    >>> _sanitize_family_name('Viikla (ent Viklund)')
    'Viikla Viklund'
    >>> _sanitize_family_name('Ahlavuo Ent.Ahlqvist')
    'Ahlavuo Ahlqvist'
    >>> _sanitize_family_name('Vuorinne Ent. Berg')
    'Vuorinne Berg'
    >>> _sanitize_family_name('Vuorinne (Berg)')
    'Vuorinne Berg'
    >>> _sanitize_family_name('Lauhikari Ent.Lübeck')
    'Lauhikari Lübeck'
    >>> _sanitize_family_name('Simojoki (ent. Simelius)')
    'Simojoki Simelius'
    >>> _sanitize_family_name('Simojoki (e. Simelius)')
    'Simojoki Simelius'
    >>> _sanitize_family_name('Simojoki e Simelius')
    'Simojoki Simelius'
    >>> _sanitize_family_name('Ent')
    'Ent'
    >>> _sanitize_family_name('Heino')
    'Heino'
    """
    new = re.sub(r'\s+\(?[eE](?:nt)?[. ]\s*', ' ', name)
    return re.sub(r'[()]', '', new)


def _generate_persons_dict(endpoint):
    """
    Generate a persons dict from person instances
    """

    results = requests.post(endpoint, {'query': QUERY_WARSA_PERSONS}).json()

    persons = defaultdict(dict)
    for person_row in results['results']['bindings']:
        person = person_row['person']['value']
        given = person_row['given']['value']
        family = person_row['family']['value']
        ranks = person_row.get('ranks', {}).get('value')
        rank_level = person_row.get('rank_level', {}).get('value')
        birth_place = person_row.get('birth_place', {}).get('value')
        birth_begin = person_row.get('birth_begin', {}).get('value')
        birth_end = person_row.get('birth_end', {}).get('value')
        death_begin = person_row.get('death_begin', {}).get('value')
        death_end = person_row.get('death_end', {}).get('value')
        death_place = person_row.get('death_place', {}).get('value')
        activity_end = person_row.get('activity_end', {}).get('value')
        units = person_row.get('units', {}).get('value')
        occupations = person_row.get('occupations', {}).get('value')

        person_dict = {
            'person': person,
            'given': given,
            'family': _sanitize_family_name(family),
            'rank': ranks.split('|') if ranks else None,
            'rank_level': int(rank_level) if rank_level else None,
            'birth_place': [birth_place] if birth_place else None,
            'birth_begin': get_date_value(birth_begin),
            'birth_end': get_date_value(birth_end),
            'death_begin': get_date_value(death_begin),
            'death_end': get_date_value(death_end),
            'death_place': [death_place] if death_place else None,
            'activity_end': get_date_value(activity_end),
            'unit': units.split('|') if units else None,
            'occupation': occupations.split('|') if occupations else None
        }
        if len([val for val in person_dict.values() if val is not None]) > 3:
            # Filter out persons with very little information
            persons[person] = person_dict
            log.debug('Using WarSampo person: {}'.format(person_dict))
        else:
            log.info('Not using person {} for record linkage because of insufficient information'.format(person))

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


def get_person_links(documents: dict, persons: dict, links):
    """
    Add person links to document dicts
    """
    for link in links:
        doc = link[0]
        per = link[1]
        if doc in documents and per in persons:
            documents[doc].update({'person': per})
            log.debug('Link found for document: {doc}'.format(doc=documents[doc]))
        else:
            log.warning('Could not find linked person: {} - {}'.format(doc, per))

    return documents


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
