import re
import sys
import logging
from collections import OrderedDict
from rdflib import URIRef
from arpa_linker.link_helper import process_stage

logger = logging.getLogger('arpa_linker.arpa')

WINTER_WAR_PERIODS = set(('<http://ldf.fi/warsa/conflicts/WinterWar>',
            '<http://ldf.fi/warsa/conflicts/InterimPeace>',))

# Roman numeral handling from http://stackoverflow.com/a/28777781/4321262

roman = OrderedDict()
roman[1000] = "M"
roman[900] = "CM"
roman[500] = "D"
roman[400] = "CD"
roman[100] = "C"
roman[90] = "XC"
roman[50] = "L"
roman[40] = "XL"
roman[10] = "X"
roman[9] = "IX"
roman[5] = "V"
roman[4] = "IV"
roman[1] = "I"


def to_roman_numeral(num):
    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num > 0:
                roman_num(num)
            else:
                break
    return "".join([a for a in roman_num(num)])


def roman_repl(m):
    return to_roman_numeral(int(m.group(1)))


def roman_repl_w_space(m):
    return '{} '.format(roman_repl(m))


def preprocessor(text, *args):

    # Remove quotation marks
    text = text.replace('"', '')

    # E.g. URR:n -> URR
    text = re.sub(r'(?<=\w):\w*', '', text)

    # KLo = Kotkan Lohko, 'Klo' will match
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
    text = re.sub(r'\b(J[RrPp])\.?(?=\d|I)', r'\1 ', text)
    # JR/55 -> JR 55
    text = re.sub(r'\b(?<=J[Rr])/(?=\d)', ' ', text)

    text = re.sub(r'\b(?<=J[RrPp] )I', '1', text)
    text = re.sub(r'\b(?<=J[RrPp] )II', '2', text)

    text = re.sub(r'\b(?<=J[RrPp] )I', '1', text)
    text = re.sub(r'\b(?<=J[RrPp] )II', '2', text)

    text = re.sub(r'\b(\d+)\.?\s*(?=/J[Rr])', roman_repl, text)

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

    text = text.strip()
    text = re.sub(r'\s+', ' ', text)

    return text


class Validator:
    def __init__(self, graph, *args, **kwargs):
        self.graph = graph
        self.known_covers = (1812, 1814,)
        self.known_wrong_covers = (1000, 2000, 3000, 4000, 6000, 10000)
        self.cover_re = r'\s*(-|valistusta|kpl|kappale(tta|en)|tonni[na]?|(m(etri([än]|stä)?|eter)?)|kg|(kilo[na]?)|([lL](itra[an])?)|mk|markkaa|vankia|(watt?i[na]?)|(nime[än])|mie(hen|stä))\b'

    def check_cover(self, cover, text):
        try:
            cover_int = int(cover)
            if cover_int > 1799 and cover_int < 1946 and cover_int not in self.known_covers:
                return False
            elif cover_int in self.known_wrong_covers:
                return False
        except ValueError:
            return True

        if re.search(r'\bn(\.|oin)?\s*' + cover, text, re.I):
            return False
        if re.search(cover + self.cover_re, text, re.I):
            return False

        logger.info('Matched by cover number ({})'.format(cover))
        return True

    def validate(self, results, text, s):
        if not results:
            return results
        original_text = self.graph.value(s, URIRef('http://www.w3.org/2004/02/skos/core#prefLabel'))
        logger.info('ORIG: {}'.format(original_text))
        war = '<{}>'.format(self.graph.value(s, URIRef('http://ldf.fi/warsa/events/related_period')))
        logger.info('War: {} ({})'.format(war, 'talvisota' if war in WINTER_WAR_PERIODS else 'jatkosota'))
        if war in WINTER_WAR_PERIODS:
            res = [r for r in results if set(r['properties'].get('war', [])) & WINTER_WAR_PERIODS]
        else:
            res = [r for r in results if set(r['properties'].get('war', [])) - WINTER_WAR_PERIODS]

        units_no_war = [r for r in results if r['properties'].get('war') is None]
        res += units_no_war

        discarded = [r['id'] for r in results if r not in res]
        if discarded:
            logger.info('Reject: wrong period {}'.format(discarded))

        units = []
        for r in res:
            if not self.check_cover(r['label'], original_text):
                discarded.append(r)
                logger.info('Reject: cover {} {}'.format(r['label'], r['id']))
                continue

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
)


if __name__ == '__main__':
    if sys.argv[1] == 'test':
        import doctest
        doctest.testmod()
        exit()

    process_stage(sys.argv, preprocessor=preprocessor, ignore=ignore, validator_class=Validator, log_level='INFO')
