#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Link WarSampo municipalities"""
import logging
from arpa_linker.arpa import process_graph
from rdflib import URIRef, Graph, Literal
from rdflib.namespace import SKOS

log = logging.getLogger(__name__)

CURRENT_MUNICIPALITIES = {
    'Ahlainen': 'Pori',
    'Aitolahti': 'Tampere',
    'Alahärmä': 'Kauhava',
    'Alastaro': 'Loimaa',
    'Alatornio': 'Tornio',
    'Angelniemi': 'Salo',
    'Anjala': 'Kouvola',
    'Anjalankoski': 'Kouvola',
    'Anttola': 'Mikkeli',
    'Artjärvi': 'Orimattila',
    'Askainen': 'Masku',
    'Bergö': 'Malax',
    'Björköby': 'Korsholm',
    'Bromarv': 'Raseborg',
    'Degerby': 'Inkoo',
    'Dragsfjärd': 'Kemiönsaari',
    'Elimäki': 'Kouvola',
    'Eno': 'Joensuu',
    'Eräjärvi': 'Orivesi',
    'Haapasaari': 'Helsinki',
    'Halikko': 'Salo',
    'Hauho': 'Hämeenlinna',
    'Haukipudas': 'Oulu',
    'Haukivuori': 'Mikkeli',
    'Hiittinen': 'Kimitoön',
    'Himanka': 'Kalajoki',
    'Hinnerjoki': 'Eura',
    'Honkilahti': 'Eura',
    'Huopalahti': 'Helsinki',
    'Iniö': 'Pargas',
    'Jaala': 'Kouvola',
    'Joutseno': 'Lappeenranta',
    'Jurva': 'Kurikka',
    'Jämsänkoski': 'Jämsä',
    'Jäppilä': 'Pieksämäki',
    'Kaarlela': 'Kokkola',
    'Kakskerta': 'Turku',
    'Kalanti': 'Uusikaupunki',
    'Kalvola': 'Hämeenlinna',
    'Kangaslampi': 'Varkaus',
    'Karhula': 'Kotka',
    'Karinainen': 'Pöytyä',
    'Karjala': 'Mynämäki',
    'Karjalohja': 'Lohja',
    'Karkku': 'Sastamala',
    'Karttula': 'Kuopio',
    # 'Karuna': 'Kemiönsaari', # Two new municipalities
    # 'Karuna': 'Sauvo',
    'Karunki': 'Tornio',
    'Kauvatsa': 'Kokemäki',
    'Keikyä': 'Sastamala',
    'Kerimäki': 'Savonlinna',
    'Kestilä': 'Siikalatva',
    'Kesälahti': 'Kitee',
    'Kiihtelysvaara': 'Joensuu',
    'Kiikala': 'Salo',
    'Kiikka': 'Sastamala',
    'Kiikoinen': 'Sastamala',
    'Kiiminki': 'Oulu',
    'Kisko': 'Salo',
    'Kiukainen': 'Eura',
    'Kodisjoki': 'Rauma',
    'Konginkangas': 'Äänekoski',
    'Korpilahti': 'Jyväskylä',
    'Korppoo': 'Pargas',
    'Kortesjärvi': 'Kauhava',
    'Kuhmalahti': 'Kangasala',
    'Kuivaniemi': 'Ii',
    'Kullaa': 'Ulvila',
    'Kulosaari': 'Helsinki',
    'Kuorevesi': 'Jämsä',
    'Kuru': 'Ylöjärvi',
    'Kuusankoski': 'Kouvola',
    'Kuusjoki': 'Salo',
    'Kuusjärvi': 'Outokumpu',
    'Kylmäkoski': 'Akaa',
    'Kymi': 'Kotka',
    'Kälviä': 'Kokkola',
    'Lammi': 'Hämeenlinna',
    'Lappee': 'Lappeenranta',
    'Lappi': 'Rauma',
    'Lauritsala': 'Lappeenranta',
    'Lehtimäki': 'Alajärvi',
    'Leivonmäki': 'Joutsa',
    'Lemu': 'Masku',
    'Liljendal': 'Loviisa',
    'Lohtaja': 'Kokkola',
    'Lokalahti': 'Uusikaupunki',
    'Luopioinen': 'Pälkäne',
    # 'Längelmäki': 'Jämsä', # Two new municipalities
    # 'Längelmäki': 'Orivesi',
    'Maaria': 'Turku',
    'Mellilä': 'Loimaa',
    'Merimasku': 'Naantali',
    'Messukylä': 'Tampere',
    'Metsämaa': 'Loimaa',
    'Mietoinen': 'Mynämäki',
    'Mouhijärvi': 'Sastamala',
    'Munsala': 'Nykarleby',
    'Muurla': 'Salo',
    'Muuruvesi': 'Kuopio',
    'Mänttä': 'Mänttä-Vilppula',
    'Nilsiä': 'Kuopio',
    'Noormarkku': 'Pori',
    'Nuijamaa': 'Lappeenranta',
    'Nummi': 'Lohja',
    'Nummi-Pusula': 'Lohja',
    'Nurmo': 'Seinäjoki',
    'Oulujoki': 'Oulu',
    'Oulunkylä': 'Helsinki',
    'Oulunsalo': 'Oulu',
    'Paattinen': 'Turku',
    'Paavola': 'Siikajoki',
    'Pattijoki': 'Raahe',
    'Perniö': 'Salo',
    'Pertteli': 'Salo',
    'Peräseinäjoki': 'Seinäjoki',
    'Petsamo': 'Tampere',
    'Pielisjärvi': 'Lieksa',
    'Pihlajavesi': 'Keuruu',
    'Piikkiö': 'Kaarina',
    'Piippola': 'Siikalatva',
    'Pohja': 'Raseborg',
    'Pulkkila': 'Siikalatva',
    'Punkaharju': 'Savonlinna',
    'Purmo': 'Pedersöre',
    'Pusula': 'Lohja',
    'Pyhäselkä': 'Joensuu',
    'Pylkönmäki': 'Saarijärvi',
    'Rantsila': 'Siikalatva',
    'Rautio': 'Kalajoki',
    'Renko': 'Hämeenlinna',
    'Revonlahti': 'Siikajoki',
    'Ristiina': 'Mikkeli',
    'Ruotsinpyhtää': 'Loviisa',
    'Ruukki': 'Siikajoki',
    'Rymättylä': 'Naantali',
    'Saari': 'Parikkala',
    'Sahalahti': 'Kangasala',
    'Salmi': 'Kuortane',
    'Saloinen': 'Raahe',
    'Sammatti': 'Lohja',
    'Savonranta': 'Savonlinna',
    'Simpele': 'Rautjärvi',
    'Sippola': 'Kouvola',
    'Snappertuna': 'Raseborg',
    'Somerniemi': 'Somero',
    'Sumiainen': 'Äänekoski',
    'Suodenniemi': 'Sastamala',
    'Suojärvi': 'Janakkala',
    'Suolahti': 'Äänekoski',
    'Suomenniemi': 'Mikkeli',
    'Suomusjärvi': 'Salo',
    'Suoniemi': 'Nokia',
    'Särkisalo': 'Salo',
    'Säräisniemi': 'Vaala',
    'Säynätsalo': 'Jyväskylä',
    'Sääksmäki': 'Valkeakoski',
    'Sääminki': 'Savonlinna',
    'Teisko': 'Tampere',
    'Temmes': 'Tyrnävä',
    'Toijala': 'Akaa',
    'Tottijärvi': 'Nokia',
    'Turtola': 'Pello',
    'Tuulos': 'Hämeenlinna',
    'Tuupovaara': 'Joensuu',
    'Tyrvää': 'Sastamala',
    'Töysä': 'Alavus',
    'Ullava': 'Kokkola',
    'Uskela': 'Salo',
    'Uukuniemi': 'Parikkala',
    'Vahto': 'Rusko',
    'Valkeala': 'Kouvola',
    'Vammala': 'Sastamala',
    'Vampula': 'Huittinen',
    'Vanaja': 'Hämeenlinna',
    'Varpaisjärvi': 'Lapinlahti',
    'Vehkalahti': 'Hamina',
    'Vehmersalmi': 'Kuopio',
    'Velkua': 'Naantali',
    'Vihanti': 'Raahe',
    'Viiala': 'Akaa',
    'Vilppula': 'Mänttä-Vilppula',
    'Virtasalmi': 'Pieksämäki',
    'Vuolijoki': 'Kajaani',
    'Vähäkyrö': 'Vaasa',
    'Värtsilä': 'Tohmajärvi',
    'Västanfjärd': 'Kimitoön',
    'Yli-Ii': 'Oulu',
    'Ylihärmä': 'Kauhava',
    'Ylikiiminki': 'Oulu',
    'Ylistaro': 'Seinäjoki',
    'Ylämaa': 'Lappeenranta',
    'Yläne': 'Pöytyä',
    'Äetsä': 'Sastamala',
    'Ähtävä': 'Pedersören kunta',
    'Esse Ähtävä': 'Pedersören kunta',
    'Koivulahti': 'Mustasaari',
    'Kvevlax Koivulahti': 'Mustasaari',
    # 'Sulva': 'Mustasaari', # Two new municipalities
    # 'Sulva': 'Vaasa',
    'Alaveteli': 'Kruunupyy',
    'Nedervetil Alaveteli': 'Kruunupyy',
    'Houtskari': 'Parainen',
    'Jepua': 'Uusikaarlepyy',
    'Kemiö': 'Kemiönsaari',
    'Maksamaa': 'Vöyri',
    'Nauvo': 'Parainen',
    'Oravainen': 'Vöyri',
    'Pernaja': 'Loviisa',
    'Pirttikylä': 'Närpiö',
    'Raippaluoto': 'Mustasaari',
    'Siipyy': 'Kristiinankaupunki',
    'Tammisaari': 'Raasepori',
    'Teerijärvi': 'Kruunupyy',
    'Ylimarkku': 'Närpiö',
    'Tiukka': 'Kristiinankaupunki',
    'Petolahti': 'Maalahti',
    'Karjaa': 'Raasepori',
    'Karjaan mlk': 'Raasepori',
    'Hyvinkään mlk': 'Hyvinkää',
    'Haagan kauppala': 'Helsinki',
    # 'Kuopion mlk': 'Kuopio', # Two new municipalities
    # 'Kuopion mlk': 'Siilinjärvi',
    'Tammisaaren mlk': 'Raasepori',
    'Koski Hl.': 'Hollola',
    'Uusikirkko Tl': 'Uusikaupunki',
    'Tenhola': 'Raasepori',
}

MUNICIPALITY_MAPPING = {
    'Kemi': URIRef('http://ldf.fi/warsa/places/municipalities/m_place_20'),
    'Pyhäjärvi Ol': URIRef('http://ldf.fi/warsa/places/municipalities/m_place_75'),
    'Pyhäjärvi Ul.': URIRef('http://ldf.fi/warsa/places/municipalities/m_place_543'),
    'Pyhäjärvi Vl': URIRef('http://ldf.fi/warsa/places/municipalities/m_place_586'),
    'Koski Tl.': URIRef('http://ldf.fi/warsa/places/municipalities/m_place_291'),
    'Koski Hl.': URIRef('http://ldf.fi/warsa/places/municipalities/m_place_391'),
    'Koski Vl.': URIRef('http://ldf.fi/warsa/places/municipalities/m_place_609'),
    'Oulun mlk': URIRef('http://ldf.fi/warsa/places/municipalities/m_place_65'),
}


def link_to_pnr(graph, target_prop, source_prop, arpa, *args, preprocess=True, new_graph=False, **kwargs):
    """
    Link municipalities to Paikannimirekisteri.
    :returns dict containing graph and stuff

    :type graph: rdflib.Graph
    :param target_prop: target property to use for new links
    :param source_prop: source property as URIRef

    >>> from unittest.mock import MagicMock
    >>> arpa = MagicMock()
    >>> g = Graph()
    >>> g.add((URIRef('foo'), SKOS.prefLabel, Literal('Foobar')))
    >>> g.add((URIRef('bar'), SKOS.prefLabel, Literal('Alatornio')))
    >>> link_to_pnr(g, 'target', 'source', arpa)['errors']
    []
    """

    def _get_municipality_label(val, uri, *args2):
        """
        Concatenate municipality labels into one string

        :param uri: municipality URI
        """
        lbls = graph.objects(uri, URIRef('http://www.w3.org/2004/02/skos/core#prefLabel'))
        return ' '.join(CURRENT_MUNICIPALITIES.get(str(l), str(l)) for l in lbls)

    if preprocess:
        preprocessor = _get_municipality_label
    else:
        preprocessor = None

    # Query the ARPA service and add the matches
    return process_graph(graph, target_prop, arpa, new_graph=new_graph, source_prop=source_prop,
                         preprocessor=preprocessor, progress=True, **kwargs)


def link_warsa_municipality(warsa_munics: Graph, labels: list):
    """
    Link municipality to Warsa

    :param warsa_munics: Municipality graph for retrieving labels
    :param labels: Labels of the municipality to be linked
    :return: list of matches

    >>> warsa_munics = Graph()
    >>> warsa_munics.add((URIRef('http://muni/Espoo'), SKOS.prefLabel, Literal("Espoo", lang='fi')))
    >>> warsa_munics.add((URIRef('http://muni/Turku'), SKOS.prefLabel, Literal("Turku")))
    >>> warsa_munics.add((URIRef('http://muni/Uusik'), SKOS.prefLabel, Literal("Uusikaarlepyyn mlk", lang='fi')))
    >>> link_warsa_municipality(warsa_munics, ['Espoo', 'Esbo'])
    rdflib.term.URIRef('http://muni/Espoo')
    >>> link_warsa_municipality(warsa_munics, ['Åbo', 'Turku'])
    rdflib.term.URIRef('http://muni/Turku')
    >>> link_warsa_municipality(warsa_munics, ['Turku'])
    rdflib.term.URIRef('http://muni/Turku')
    >>> link_warsa_municipality(warsa_munics, ['Turku', 'Espoo'])
    >>> link_warsa_municipality(warsa_munics, ['Uusikaarlepyyn kunta'])
    rdflib.term.URIRef('http://muni/Uusik')
    """
    warsa_matches = []

    for lbl in labels:
        log.debug('Finding Warsa matches for municipality {}'.format(lbl))
        lbl = str(lbl).strip()
        munmap_match = MUNICIPALITY_MAPPING.get(lbl)
        if munmap_match:
            log.debug('Found predefined mapping for {}: {}'.format(lbl, munmap_match))
            warsa_matches += [munmap_match]
        else:
            warsa_matches += list(warsa_munics[:SKOS.prefLabel:Literal(lbl)])
            warsa_matches += list(warsa_munics[:SKOS.prefLabel:Literal(lbl, lang='fi')])

        if not warsa_matches:
            log.debug('Trying with mlk: {}'.format(lbl))
            warsa_matches += list(warsa_munics[:SKOS.prefLabel:Literal(lbl.replace(' kunta', ' mlk'))])
            warsa_matches += list(warsa_munics[:SKOS.prefLabel:Literal(lbl.replace(' kunta', ' mlk'), lang='fi')])

    if len(warsa_matches) == 1:
        match = warsa_matches[0]
        log.info('Found {lbl} municipality Warsa URI {s}'.format(lbl=labels, s=match))
        return match

    elif len(warsa_matches) == 0:
        log.info("Couldn't find Warsa URI for municipality {lbl}".format(lbl=labels))
    else:
        log.warning('Found multiple Warsa URIs for municipality {lbl}: {s}'.format(lbl=labels, s=warsa_matches))

    return None


