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

from jellyfish import jaro_winkler
from rdflib import Graph, URIRef, RDF
from rdflib.util import guess_format

log = logging.getLogger(__name__)

occupation_mapping = {
    'ajom.': 'ajomies',
    'apum.': 'apumies',
    'asiap.': 'asiapoika',
    'au': 'aliupseeri',
    'autoh.': 'autohuoltomies',
    'autokoulun om.': 'autokoulun omistaja',
    'autonk.': 'autonkuljettaja',
    'aut.kulj.': 'autonkuljettaja',
    'bet.työm.': 'betonityömies',
    'di': 'diplomi-insinööri',
    'dipl.ins.': 'diplomi-insinööri',
    'ekon.': 'ekonomi',
    'hansikk.leikk.': 'hansikastyöntekijä',
    'holanterin etum': 'holanterin etumies',
    'henkiv.tarkast.': 'henkivakuutustarkastastaja',
    'hevosm.': 'hevosmies',
    'huoltom.': 'huoltomies',
    'fk': 'filosofian kandidaatti',
    'fm': 'filosofian maisteri',
    'ins.': 'insinööri',
    'junam.': 'junamies',
    'järj.m.': 'järjestysmies',
    'kassak:piseppä': 'kassakaappiseppä',
    'kalast.': 'kalastaja',
    'kanta-au.': 'kanta-aliupseeri',
    'kaup.hoit.': 'kaupanhoitaja',
    'kaup.maanmitt.': 'kaupungin maanmittaaja',
    'kaup.työm.': 'kaupungin työntekijä',
    'kaup.voud.apul.': 'kaupunginvoudin apulainen',
    'kemik.kaup.om.': 'kemikalionomistaja',
    'kivenhakk.': 'kivenhakkaaja',
    'konst.': 'konstaapeli',
    'kun.kod.joht.': 'kunnalliskodin johtaja',
    'laitosm.': 'laitosmies',
    'lent.teht.työm.': 'lentokonetehtaan työmies',
    'liikk.harj.': 'liikkeenharjoittaja',
    'linj.aut.rahast': 'linja-auton rahastaja',
    'linjam.': 'linjamies',
    'lohkotil.': 'lohkotilallinen',
    'lukiol.': 'lukiolainen',
    'lämm.': 'lämmittäjä',
    'lääk.': 'lääkäri',
    'lääk.vääp.': 'lääkintävääpeli',
    'korj.pajantyöm.': 'korjauspajan työntekijä',
    'koulul.': 'koululainen',
    'kuolul.': 'koululainen',
    'maanvilj.tytär': 'maanviljelijän tytär',
    'maanvilj.koul.': 'maanviljelyskoululainen',
    'maatal.teknikko': 'maatalousteknikko',
    'majatalon pit.': 'majatalonpitäjä',
    'merim.': 'merimies',
    'met.jyrsijä': 'metallijyrsijä',
    'met.painaja': 'metallipainaja',
    'met.sorvari': 'metallisorvari',
    'mets.hoid.neuv.': 'metsänhoidonneuvoja',
    'muur.': 'muurari',
    'mv': 'maanviljelijä',
    'mv.': 'maanviljelijä',
    'mv.p': 'maanviljelijän poika',
    'mv.p.': 'maanviljelijän poika',
    'mv.pka': 'maanviljelijän poika',
    'mv. pka': 'maanviljelijän poika',
    'mv.pienvilj.': 'pienviljelijä',
    'myym.hoit.': 'myymälän hoitaja',
    'mäkitup.': 'mäkitupalainen',
    'mökk.pka': 'mökkiläisen poika',
    'nti.': 'neiti',
    'opisk.': 'opiskelija',
    'opisk. yo.': 'ylioppilas',
    'opisk.yo.': 'ylioppilas',
    'opisk.yo': 'ylioppilas',
    'opett.': 'opettaja',
    'opp.': 'oppilas',
    'palstatilall.pa': 'palstatilallisen poika',
    'pientil.': 'pientilallinen',
    'peräm.': 'perämies',
    'piir.apulainen': 'piirtäjän apulainen',
    'piirim.': 'piirimies',
    'porom.': 'poromies',
    'porolappal.pka': 'porosaamelaisen poika',
    'poliisikonst': 'poliisikonstaapeli',
    'poliisikonst.': 'poliisikonstaapeli',
    'posl.teht.työm.': 'posliinitehtaan työläinen',
    'postelj.': 'posteljooni',
    'postink.': 'postinkantaja',
    'prässim.': 'prässimies',
    'putkim.': 'putkimies',
    'putkias.apul.': 'putkiasentajan apulainen',
    'pp.mekaankko': 'polkupyoramekaanikko',
    'puutarh.': 'puutarhuri',
    'rad.työm.tek.': 'radiotyömies',
    'rahast.': 'rahastaja',
    'rak.alalla': 'rakennustyöläinen',
    'rakennus-': 'rakennustyöläinen',
    'rautatiel.': 'rautatieläinen',
    'sem.opp.': 'seminaarin oppilas',
    'sorv.apul.': 'sorvaajan apulainen',
    'suut.': 'suutari',
    'taloll.pka': 'talollisen poika',
    'talollisen pka': 'talollisen poika',
    'tal.om.': 'talonomistaja',
    'tal.omist.': 'talonomistaja',
    'tal.pka': 'talollisen poika',
    'taloll.': 'talollinen',
    'teht.vart.': 'tehdasvartija',
    'teht.virk.': 'tehdasvirkailija',
    'tekn.ylioppilas.': 'tekniikan ylioppilas',
    'terv.hoid.tark.': 'terveydenhoidon tarkastaja',
    'teurast.': 'teurastaja',
    'tilall.pka': 'tilallisen poika',
    'tilall. pka': 'tilallisen poika',
    'tekstil.ins.': 'tekstiili-insinööri',
    'teht.edust.': 'tehtaan edustaja',
    'tehd.työl.': 'tehdastyöläinen',
    'teht.työm.': 'tehdastyöläinen',
    'teht.työl.': 'tehdastyöläinen',
    'tsto apul.': 'toimistoapulainen',
    'tullim.': 'tullimies',
    'turp.hoit.apul.': 'turbiininhoitajan apulainen',
    'ulosottom.': 'ulosottomies',
    'valok.': 'valokuvaaja',
    'varastom.': 'varastomies',
    'viilankarkais.': 'viilankarkaisija',
    'vinssim.': 'vinssimies',
    'vuokr.': 'vuokraaja',
    'yhteisk.tiet.yo': 'yhteiskuntatieteiden ylioppilas',
    'yo.': 'ylioppilas',
    'yo': 'ylioppilas',
}

occupation_substitutions = [
    (r'^(agr\. *)(.+)', r'agronomian \2'),
    (r'^(apt\.)(.+)', r'apteekin\2'),
    (r'^(apul\.)(.+)', r'apulais\2'),
    (r'^(bens\.as\.)(.+)', r'bensiiniaseman\2'),
    (r'^(dipl\.)(.+)', r'diplomi\2'),
    (r'^(el\.lääk(et)?\. *)(.+)', r'eläinlääketieteen \2'),
    (r'^(farm\. *)(.+)', r'farmasian \2'),
    (r'^(fil\. *)(.+)', r'filosofian \2'),
    (r'^(hall.oik. *)(.+)', r'hallinto-oikeuden \2'),
    (r'^(ho:n *)(.+)', r'hovioikeuden \2'),
    (r'^(huonek\.)(.+)', r'huonekalu\2'),
    (r'^(huv\. *)(.+)', r'huvilan \2'),
    (r'^(höyryk\. *)(.+)', r'höyrykone \2'),
    (r'^(?:its\.|itsell\.)(.*)', r'itsellinen\1'),
    (r'^(joht\. *)(.*)', r'johtaja\2'),
    (r'^(kansak\. *)(.+)', r'kansakoulun \2'),
    (r'^(kauppat\. *)(.+)', r'kauppatieteiden \2'),
    (r'^(kirjansit\.)(.+)', r'kirjansitomo\2'),
    (r'^(kun\.kod\. )(.+)', r'kunnalliskodin \2'),
    (r'^(lainop\. *)(.+)', r'lakitieteen \2'),
    (r'^(lakit\. *)(.+)', r'lakitieteen \2'),
    (r'^(lentok\. *)(.+)', r'lentokone \2'),
    (r'^(liikk\. *)(.+)', r'liikkeen\2'),
    (r'^(l\-autoas\. *)(.+)', r'linja-autoaseman \2'),
    (r'^(?:lin|linn)(?:\.)(.+)', r'linnoitus\1'),
    (r'^(lääket\. *)(.+)', r'lääketieteen \2'),
    (r'^(maat\.metsät\. *)(.+)', r'maa- ja metsätaloustieteiden \2'),
    (r'^(maat\.)(.+)', r'maatalous\2'),
    (r'^(maatal\.)(.+)', r'maatalous\2'),
    (r'^(makk\.)(.+)', r'makkara\2'),
    (r'^(metsät\. *)(.+)', r'metsätieteen \2'),
    (r'^(metsänh\.)(.+)', r'metsänhoitaja\2'),
    (r'^(mielis\.)(.+)', r'mielisairaan\2'),
    (r'^(mökkil\.)(.*)', r'mökkiläisen \2'),
    (r'^(mv\.?)(.+)', r'maanviljelijän\2'),
    (r'^(?:palstatil|palst)(?:\. *)(.+)', r'palstatilallisen \1'),
    (r'^(nuor\. *)(.+)', r'nuorempi \2'),
    (r'^(pap\.)(.+)', r'paperi\2'),
    (r'^(pienv\. *)(.+)', r'pienviljelijän \2'),
    (r'^(piir\. *)(.+)', r'piirtäjän \2'),
    (r'^(pol\.)(.+)', r'poliisi\2'),
    (r'^(puutarh\. *)(.+)', r'puutarha\2'),
    (r'^(puh\. *)(.+)', r'puhelin\2'),
    (r'^(rak\. *)(.+)', r'rakennus\2'),
    (r'^(ratav\. *)(.+)', r'ratavartijan \2'),
    (r'^(rullausk\. *)(.+)', r'rullauskoneen \2'),
    (r'^(sair\.)(.+)', r'sairaan\2'),
    (r'^(sellul\.)(.+)', r'selluloosa\2'),
    (r'^(sk(\.|\-|:) *)(.+)', r'suojeluskunta\2'),
    (r'^(sot\. *)(.+)', r'sotilas\2'),
    (r'^(sotap\.)(.+)', r'sotapoliisi\2'),
    (r'^(taloll\. *)(.+)', r'talollisen \2'),
    (r'^(tekn\. *)(.+)', r'tekniikan \2'),
    (r'^(teol\. *)(.+)', r'teologian \2'),
    (r'^(teoll\.)(.+)', r'teollisuus\2'),
    (r'^(til\. *)(.+)', r'tilallisen \2'),
    (r'^(urh\.)(.+)', r'urheilu\2'),
    (r'^(vak\.)(.+)', r'vakuutus\2'),
    (r'^(valt\.tiet\. *)(.+)', r'valtiotieteen \2'),
    (r'^(var\. *)(.+)', r'varaston \2'),
    (r'^(vet\. *)(.+)', r'veturin\2'),
    (r'^(voim\. *)(.+)', r'voimistelun\2'),
    (r'^(vt\. *)(.+)', r'virkaa tekevä \2'),
    (r'^(vuokr\. *)(.+)', r'vuokraajan \2'),
    (r'^(ylim\. *)(.+)', r'ylimääräinen  \2'),
    (r'^(yo\-)(.+)', r'ylioppilas\2'),

    (r'(.*)(harj|harjoitt)($|\.)', r'\1harjoittelija'),
    (r'(.*)(insin\. ?)(.*)', r'\1insinööri\3'),
    (r'(.*)(oik\.)', r'\1oikeus'),
    (r'(.*)(?:opett|opet)(?:\.)(.*)', r'\1opettaja\2'),
    (r'(.*)(pka)($|\.)', r'\1poika'),
    (r'(.*)(tekn\.)(.*)', r'\1teknikko\3'),
    (r'(.*)(työnj)($|\.)', r'\1työnjohtaja'),
    (r'(.*)(työnjoh)($|\.)', r'\1työnjohtaja'),
    (r'(.*)(yo)($|\.)', r'\1ylioppilas'),
    (r'(.*)(työm)($|\.)', r'\1työmies'),

    (r'(.+)(ausk\.)', r'\1auskultantti'),
    (r'(.+)(apul\.)', r'\1apulainen'),
    (r'(.+)(hoit\.)', r'\1hoitaja'),
    (r'(.+)(ins\.)$', r'\1insinööri'),
    (r'(.+)(isänn\.)$', r'\1isännöitsijä'),
    (r'(.+)(joht)($|\.)', r'\1johtaja'),
    (r'(.+)(kand\.)', r'\1kandidaatti'),
    (r'(.+)(kok\.)', r'\1kokelas'),
    (r'(.+)(kaup\.)', r'\1kauppias'),
    (r'(.+)(kapt\.)', r'\1kapteeni'),
    (r'(.+)(käytt\.)', r'\1käyttäjä'),
    (r'(.+)kulj\.?$', r'\1kuljettaja'),
    (r'(.+)(lääk\.)$', r'\1lääkäri'),
    (r'(.+)(lis\.)$', r'\1lisensiaatti'),
    (r'(.+)(maist\.?)$', r'\1maisteri'),
    (r'(.+)(mekaan\.)', r'\1mekaanikko'),
    (r'(.+)(maal\.)', r'\1maalari'),
    (r'(.+)(mek\.)', r'\1mekaanikko'),
    (r'(.+)(mest\.)', r'\1mestari'),
    (r'(.+)(montt\.)', r'\1monttööri'),
    (r'(.+)(myym\.)', r'\1myymälä'),
    (r'(.+)(rakent\.)', r'\1rakentaja'),
    (r'(.+)(työntek\.)', r'\1työntekijä'),
    (r'(.+)(työnt\.)', r'\1työntekijä'),
    (r'(.+)(palv\.)', r'\1palvelija'),
    (r'(.+)(pääll|pääl)($|\.)', r'\1päällikkö'),
    (r'(.+)(peräm\.)', r'\1perämies'),
    (r'(.+)(\.| )(p|(pka))($|\.)', r'\1 poika'),
    (r'(.+)(omist\.)$', r'\1omistaja'),
    (r'(.+)(opisk)($|\.)', r'\1opiskelija'),
    (r'(.+)(opistol\.)', r'\1opistolainen'),
    (r'(.+)(opp\.)', r'\1oppilas'),
    (r'(.+)(vart\.)', r'\1vartija'),
    (r'(.+)(virk\.)', r'\1virkailija'),
    (r'(.+)(reht\.)$', r'\1rehtori'),
    (r'(.+)(til\.)', r'\1tilallinen'),
    (r'(.+)(työl\.)', r'\työläinen'),
    (r'(.+)(toim\.)', r'\1toimittaja'),
    (r'(.+)(ups\.)', r'\1upseeri'),
]


def _harmonize_labels(literal, sep, valuemap, subs):
    literal = str(literal).strip()

    if literal == '-':
        return ''

    processed = []
    for s in re.split(sep, literal):
        if not s:
            continue

        s = s.strip()
        if s in valuemap:
            value = valuemap[s]
        else:
            value = s
            for sub in subs:
                value = re.sub(sub[0], sub[1], value)

        if value:
            processed.append(value)

    return processed


def link_occupations(graph, endpoint, source_property: URIRef, target_property: URIRef, resource_type: URIRef,
                     sep=r'[,/]', score_threshold=0.88, subs=occupation_substitutions, valuemap=occupation_mapping):
    """
    Link occupations in graph based on string similarity. Each property value is compared against all values in
    the occupation ontology.

    :param graph: Data in RDFLib Graph object
    :param endpoint: SPARQL endpoint
    :param source_property: Source property for linking
    :param target_property: Property to use for writing found links
    :param resource_type: Class of resources to be linked
    :param sep: separator(s) as regular expression
    :param score_threshold: score threshold for linking occupations based on string similarity
    :param subs: Regular expression substitutions for value harmonization as a list of tuples
    :param valuemap: dictionary for direct mapping of values
    :return: RDFLib Graph with updated links
    """

    query = """
        PREFIX text: <http://jena.apache.org/text#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT ?id ?label {{
            GRAPH <http://ldf.fi/warsa/occupations> {{
                ?id a <http://ldf.fi/schema/ammo/Concept> .
                ?id skos:prefLabel|skos:altLabel ?label .
            }}
         }}
    """

    def find_best_match(occupation_do, occupation_literal):
        best_score = 0
        best_uri = None

        for uri, label in occupation_do:
            match_score = jaro_winkler(label, occupation_literal)
            if match_score > best_score:
                best_uri = uri
                best_score = match_score

        return best_uri, best_score

    def get_occupation_link(occupation_do, linked_occupations, occupation_str, original):
        if occupation_str in linked_occupations:
            uri = linked_values[occupation_str]
        else:
            uri, score = find_best_match(occupation_do, occupation_str)
            if uri and occupation_str not in linked_occupations:
                if score > score_threshold:
                    linked_occupations[occupation_str] = uri
                    log.debug('Accepted match for occupation {o} ({orig}): {uri} (score {s:.2f})'.format(
                        o=occupation_str, orig=original, uri=uri, s=score))
                else:
                    linked_occupations[occupation_str] = None
                    log.debug('No match found for occupation {o} ({orig}) (best match {uri} - score {s:.2f})'.format(
                        o=occupation_str, orig=original, uri=uri, s=score))
                    uri = None

        return uri

    results = requests.post(endpoint, {'query': query}).json()

    links = Graph()
    linked_values = {}

    occupation_do_tuples = [(res['id']['value'], res['label']['value']) for res in results['results']['bindings']]
    log.debug('Got {} occupations'.format(len(occupation_do_tuples)))

    unlinked_occupations = defaultdict(int)

    for person in graph[:RDF.type:resource_type]:
        literals = graph.objects(person, source_property)
        for literal in literals:
            harmonized = _harmonize_labels(literal, sep, valuemap, subs)
            for occupation in harmonized:
                occupation_uri = get_occupation_link(occupation_do_tuples, linked_values, occupation, literal)
                if occupation_uri:
                    links.add((person, target_property, URIRef(occupation_uri)))
                else:
                    unlinked_occupations[occupation] += 1

    for literal, count in sorted(unlinked_occupations.items(), key=operator.itemgetter(1, 0)):
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
