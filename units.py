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


def preprocessor(text, *args):

    # E.g. URR:n -> URR
    text = re.sub(r'(?<=\w):\w+', '', text)

    # KLo = Kotkan Lohko, 'Klo' will match
    text = re.sub(r'\bKlo\b', 'klo', text)

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
    text = re.sub(r'([IV])\.\s*(?=AKE?)', r'\1 ', text)

    # Rannikkoprikaati
    text = re.sub(r'Laat\.?\s*R\.?\s*[Pp]r\.?', r'Laat.RPr.', text)
    text = re.sub(r'(?<=n )R[Pp]r\.?', r'rannikkoprikaati', text)
    text = re.sub(r'E/II R[Pp]r\.?', r'2.RPr.E', text)

    # Kenttäsairaala
    text = re.sub(r'([Kk]enttäsairaala\w*|KS)-?\s+[A-Z]?(\d+)', r'\2. \1', text)

    # Match super unit as well
    for m in re.finditer(r'(?<=/)([A-Z]+\.?\s*\d+)', text):
        text += ' # {}'.format(m.group(0))

    for m in re.finditer(r'(?<=/)([0-9]+\.\s*\w+)', text):
        text += ' # {}'.format(m.group(0))

    text = text.strip()
    text = re.sub(r'\s+', ' ', text)

    return text


class Validator:
    def __init__(self, graph, *args, **kwargs):
        self.graph = graph

    def validate(self, results, text, s):
        if not results:
            return results
        war = '<{}>'.format(self.graph.value(s, URIRef('http://ldf.fi/warsa/events/related_period')))
        logger.info('War: {} ({})'.format(war, 'talvisota' if war in WINTER_WAR_PERIODS else 'jatkosota'))
        if war in WINTER_WAR_PERIODS:
            res = [r for r in results if set(r['properties'].get('war', [])) & WINTER_WAR_PERIODS]
        else:
            res = [r for r in results if set(r['properties'].get('war', [])) - WINTER_WAR_PERIODS]

        units_no_war = [r for r in results if r['properties'].get('war') is None]
        res += units_no_war

        discarded = [r['id'] for r in res if r not in results]
        if discarded:
            logger.info('Reject: wrong period {}'.format(discarded))

        units = []
        for r in res:
            try:
                cover = int(r['label'])
                if cover > 1938 and cover < 1946:
                    logger.info('Reject: cover number is year {}'.format(r))
                    discarded.append(r)
                    continue
            except ValueError:
                pass
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
    'Turku'
)


if __name__ == '__main__':
    if sys.argv[1] == 'test':
        import doctest
        doctest.testmod()
        exit()

    process_stage(sys.argv, preprocessor=preprocessor, ignore=ignore, validator_class=Validator, log_level='INFO')
