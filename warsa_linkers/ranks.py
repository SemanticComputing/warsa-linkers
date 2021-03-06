#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Link rank strings to WarSampo rank ontology"""
import re
import requests

from rdflib import Graph, RDF, URIRef


def link_ranks(graph, endpoint, source_prop, target_prop, class_uri):
    """
    Link military ranks in graph.

    :param graph: Data in RDFLib Graph object
    :param endpoint: Endpoint to query military ranks from
    :param source_prop:
    :param target_prop:
    :param class_uri:
    :return: RDFLib Graph with updated links
    """

    def preprocess(literal):
        value = str(literal).strip()
        return rank_mapping.get(value, value)

    rank_mapping = {
        'aliluutn': 'aliluutnantti',
        'aliluutn.': 'aliluutnantti',
        'alisot.ohj.': 'Alisotilasohjaaja',
        'alisot.virk.': 'Alisotilasvirkamies',
        'asemest.': 'asemestari',
        'au.opp.': 'aliupseerioppilas',
        'el.lääk.ev.luutn.': 'Eläinlääkintäeverstiluutnantti',
        'el.lääk.kapt.': 'Eläinlääkintäkapteeni',
        'el.lääk.maj.': 'Eläinlääkintämajuri',
        'GRUF': 'Gruppenführer',
        'II lk. nstm.': 'Toisen luokan nostomies',
        'ins.kapt.': 'Insinöörikapteeni',
        'ins.kapt.luutn.': 'Insinöörikapteeniluutnantti',
        'ins.luutn.': 'Insinööriluutnantti',
        'ins.maj.': 'Insinöörimajuri',
        'is-mies': 'Ilmasuojelumies',
        'is.stm.': 'Ilmasuojelusotamies',
        'kaart': 'stm',
        'kapt.luutn.': 'kapteeniluutnantti',
        'kom.kapt.': 'komentajakapteeni',
        'lääk.alik': 'lääkintäalikersantti',
        'lääk.alikers.': 'Lääkintäalikersantti',
        'lääk.kapt.': 'Lääkintäkapteeni',
        'lääk.kers.': 'Lääkintäkersantti',
        'lääk.korpr.': 'Lääkintäkorpraali',
        'lääk.lotta': 'Lääkintälotta',
        'lääk.maj.': 'Lääkintämajuri',
        'lääk.stm': 'lääkintäsotamies',
        'lääk.stm.': 'Lääkintäsotamies',
        'lääk.vääp.': 'Lääkintävääpeli',
        'lääk.virk.': 'Lääkintävirkamies',
        'lentomek.': 'Lentomekaanikko',
        'linn.työnjoht.': 'Linnoitustyönjohtaja',
        'merivart.': 'Merivartija',
        'mus.luutn.': 'Musiikkiluutnantti',
        'OSTUF': 'Obersturmführer',
        'paik.pääll.': 'Paikallispäällikkö',
        'pans.jääk.': 'Panssarijääkäri',
        'pursim.': 'pursimies',
        'rajavääp.': 'rajavääpeli',
        'RTTF': 'Rottenführer',
        'sair.hoit.': 'Sairaanhoitaja',
        'sair.hoit.opp.': 'Sairaanhoitajaoppilas',
        'SCHTZ': 'Schütze',
        'sivili': 'siviili',
        'sk.korpr.': 'Suojeluskuntakorpraali',
        'sot.alivirk.': 'Sotilasalivirkamies',
        'sot.inval.': 'Sotainvalidi',
        'sot.kotisisar': 'Sotilaskotisisar',
        'sot.past.': 'Sotilaspastori',
        'sot.pka': 'Sotilaspoika',
        'sot.poika': 'Sotilaspoika',
        'sotilasmest.': 'Sotilasmestari',
        'STRM': 'Sturmmann',
        'ups.kok': 'upseerikokelas',
        'ups.kok.': 'Upseerikokelas',
        'ups.opp.': 'Upseerioppilas',
        'USCHA': 'Unterscharführer',
        'USTUF': 'Untersturmführer',
        'ylihoit.': 'Ylihoitaja',
        'ylivääp.': 'Ylivääpeli',
    }

    # Works in Fuseki because SAMPLE returns the first value and text:query sorts by score
    query = """
        PREFIX text: <http://jena.apache.org/text#>
        SELECT ?rank (SAMPLE(?id_) AS ?id) {{
            VALUES ?rank {{ "{values}" }}
            GRAPH <http://ldf.fi/warsa/ranks> {{
                ?id_ text:query ?rank .
                ?id_ a <http://ldf.fi/schema/warsa/Rank> .
            }}
        }} GROUP BY ?rank
    """

    rank_literals = set(map(preprocess, graph.objects(None, source_prop)))

    results = requests.post(endpoint, {'query': query.format(values='" "'.join(rank_literals))}).json()

    rank_links = Graph()
    ranks = {}
    for rank in results['results']['bindings']:
        ranks[rank['rank']['value']] = rank['id']['value']

    for person in graph[:RDF.type:class_uri]:
        rank_literal = preprocess(str(graph.value(person, source_prop)))
        if rank_literal in ranks:
            rank_links.add((person, target_prop, URIRef(ranks[rank_literal])))

    return rank_links
