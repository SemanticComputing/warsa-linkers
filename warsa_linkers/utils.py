#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Linking utils"""

import logging
import time

from SPARQLWrapper import SPARQLWrapper

log = logging.getLogger(__name__)


def query_sparql(sparql_obj: SPARQLWrapper):
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

    return results
