import os
import re
import sys
import logging
import roman
from rdflib import URIRef
from arpa_linker.link_helper import process_stage
from warsa_linkers.persons import get_ranked_matches

logger = logging.getLogger('arpa_linker.arpa')

WINTER_WAR_PERIODS = set(('<http://ldf.fi/warsa/conflicts/WinterWar>',
            '<http://ldf.fi/warsa/conflicts/InterimPeace>',))


def get_query_template():
    with open(os.path.join(os.path.dirname(__file__), 'units.sparql')) as f:
        return f.read()


def roman_repl(m):
    return roman.toRoman(int(m.group(1)))


def roman_repl_w_space(m):
    return '{} '.format(roman_repl(m))


def int_from_roman_repl(m):
    try:
        return str(roman.fromRoman(m.group(1)))
    except roman.InvalidRomanNumeralError:
        return ''


def get_match_scores(results):
    rd = get_ranked_matches(results)
    res = {}
    for k, v in rd.items():
        for uri in v['uris']:
            res[uri] = False if v['score'] < 0 else True

    return res


def preprocessor(text, *args):

    # Remove quotation marks
    text = text.replace('"', '')

    # E.g. URR:n -> URR
    text = re.sub(r'(?<=\w):\w*', '', text)

    # Remove whitespace before and after a /
    text = re.sub(r'\s*/\s*', '/', text)

    # KLo = Kotkan Lohko, 'Klo' would match
    text = re.sub(r'\b[Kk]lo\b', '', text)

    # TykK
    text = re.sub(r'\b[Tt]yk\.K\b', 'TykK', text)

    # Div -> D
    text = re.sub(r'\b[Dd]iv\.\s*', 'D ', text)

    # D, Pr, KS
    text = re.sub(r'\b(\d+)[./]?\s*(?=D|Pr\b|KS\b)', r'\1. ', text)

    # J.R. -> JR
    text = re.sub(r'\bJ\.[Rr]\.?\s*(?=\d)', 'JR ', text)
    # JR, JP
    text = re.sub(r'\b(J[RrPp])\.?(?=\d|I|V)', r'\1 ', text)
    # JR/55 -> JR 55
    text = re.sub(r'\b(?<=J[Rr])/(?=\d)', ' ', text)

    text = re.sub(r'\b(?<=J[RrPp] )([IVX]+)', int_from_roman_repl, text)

    text = re.sub(r'\b(\d+)\.?\s*/J[Rr]', r'\1./JR', text)

    # AK, AKE
    text = re.sub(r'\b(\d+)\.?\s*(?=AKE)', roman_repl_w_space, text)
    text = re.sub(r'([IV])\.\s*(?=AKE?)', r'\1 ', text)
    # Rannikkoprikaati
    text = re.sub(r'Laat\.?\s*R\.?\s*[Pp]r\.?', r'Laat.RPr.', text)
    text = re.sub(r'(?<=n )R[Pp]r\.?', r'rannikkoprikaati', text)
    text = re.sub(r'E/II R[Pp]r\.?', r'2.RPr.E', text)

    # Kenttäsairaala
    text = re.sub(r'([Kk]enttäsairaala\w*|KS)-?\s+[A-Z]?(\d+)', r'\2. \1', text)

    # LeLv/LLv
    text = re.sub(r'\b(Le?Lv)\.?\s*(\d+)', r'LLv \2 # LeLv \2', text, flags=re.I)
    text = re.sub(r'\b(\d+)\.?\s*(Le?Lv)', r'LLv \1 # LeLv \1', text, flags=re.I)

    # Swedish
    text = re.sub(r"´s", '', text)

    text = re.sub(r'[´`]', '', text)

    text = text.strip()
    text = re.sub(r'\s+', ' ', text)

    return text


class Validator:
    accept_cover = True
    filter_by_length = True

    def __init__(self, graph, *args, **kwargs):
        self.graph = graph
        self.known_covers = (1812, 1814,)
        self.known_wrong_covers = (1000, 2000, 3000, 4000, 6000, 10000, 16)
        self.cover_re = r'\s*(-|valistusta|kpl|kappale(tta|en)|tonni[na]?|(m(etri([än]|stä)?|eter)?)|kg|(kilo[na]?)|([lL](itra[an])?)|mk|markkaa|vankia|(watt?i[na]?)|(nime[än])|mie(hen|stä))\b'

    def check_cover(self, cover, text):
        try:
            cover_int = int(cover)
            if cover_int > 1799 and cover_int < 1946 and cover_int not in self.known_covers:
                return False
            elif cover_int in self.known_wrong_covers:
                return False
        except ValueError:
            return None

        if re.search(r'\bn(\.|oin)?\s*' + cover, text, re.I):
            return False
        if re.search(cover + self.cover_re, text, re.I):
            return False

        logger.info('Matched by cover number ({})'.format(cover))
        return True

    def get_units_by_war(self, results, war):
        if war in WINTER_WAR_PERIODS:
            res = [r for r in results if set(r['properties'].get('war', [])) & WINTER_WAR_PERIODS]
        else:
            res = [r for r in results if set(r['properties'].get('war', [])) - WINTER_WAR_PERIODS]

        return res

    def validate(self, results, text, s):
        if not results:
            return results
        original_text = self.graph.value(s, URIRef('http://www.w3.org/2004/02/skos/core#prefLabel'))
        logger.info('ORIG: {}'.format(original_text))

        war = '<{}>'.format(self.graph.value(s, URIRef('http://ldf.fi/schema/warsa/events/related_period')))
        logger.info('War: {} ({})'.format(war, 'talvisota' if war in WINTER_WAR_PERIODS else 'jatkosota'))

        units_no_war = [r for r in results if r['properties'].get('war') is None]
        res = self.get_units_by_war(results, war) + units_no_war

        discarded = [r['id'] for r in results if r not in res]
        if discarded:
            logger.info('Reject: wrong period {}'.format(discarded))

        units = []
        ranked_matches = get_match_scores(res)
        for r in res:
            cover_check = self.check_cover(r['label'] or '', original_text or '')
            if cover_check is False or cover_check is True and self.accept_cover is False:
                discarded.append(r)
                logger.info('Reject: cover {} {}'.format(r['label'], r['id']))
            elif self.filter_by_length and ranked_matches.get(r['id'], True) is False:
                discarded.append(r)
                logger.info('Reject: short match {} {}'.format(r['label'], r['id']))
            else:
                units.append(r)

        if discarded:
            logger.info('Rejected: {}'.format(discarded))

        return units


ignore = (
    'Puolukka',
    'Otava',
    'Vaaka',
    'Varsa',
    'Neito',
    'Voima',
    'Turku',
    'suursaari',
    'tor',
    'vrt',
    'ylipäällikkö',
    'rauma',
)


if __name__ == '__main__':
    if sys.argv[1] == 'test':
        import doctest
        doctest.testmod()
        exit()

    special_args = sys.argv[-2:]
    if 'no_cover' in special_args:
        Validator.accept_cover = False
        sys.argv.remove('no_cover')
    if 'no_length_filter' in special_args:
        Validator.filter_by_length = False
        sys.argv.remove('no_length_filter')

    prep = preprocessor
    if sys.argv[-1] == 'naive':
        prep = None
        ignore = None
        sys.argv.pop()

    if sys.argv[4] == 'battle_unit_linked.ttl':
        ignore = None

    process_stage(sys.argv, preprocessor=prep, ignore=ignore, validator_class=Validator, log_level='INFO')
