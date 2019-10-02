import re
import sys
from arpa_linker.link_helper import process_stage


ISLAND_TYPE = 'http://ldf.fi/pnr-schema#place_type_350'
ISLAND_TYPE_URI = '<{}>'.format(ISLAND_TYPE)

ISLANDS = [
    'Ahvenanmaa',
    'Ulko-Tammio',
    'Morgonlandet'
]


LABEL_TO_PLACE = {
    'Rautalahti': 'http://ldf.fi/warsa/places/karelian_places/k_place_33031',
    'Saarijärvi': 'http://ldf.fi/warsa/places/karelian_places/k_place_37458',
    'Murtovaara': 'http://ldf.fi/pnr/P_10558843',
    'Myllykoski': 'http://ldf.fi/pnr/P_10130817',
    'Kuosmala': 'http://ldf.fi/pnr/P_10392668',
    'Tyrävaara': 'http://ldf.fi/pnr/P_10213175',
    'Kivivaara': 'http://ldf.fi/pnr/P_10543550',
    'Kotka': 'http://ldf.fi/pnr/P_10878654',
    'Malmi': 'http://ldf.fi/pnr/P_10012991',
    'Kylänmäki': 'http://ldf.fi/pnr/P_10530797',
    'Käpylä': 'http://ldf.fi/pnr/P_10342681',
}


class Validator:
    def __init__(self, graph, *args, **kwargs):
        self.graph = graph

    def validate(self, results, text, s):
        if not results:
            return results
        res = []
        for place in results:
            label = place.get('label')
            is_island = ISLAND_TYPE_URI in place.get('properties', {}).get('type', [])
            if is_island and label not in ISLANDS:
                continue
            if "Lieks" in text and label == "Nurmijärvi":
                place['id'] = 'http://ldf.fi/pnr/P_10588451'
            else:
                place['id'] = LABEL_TO_PLACE.get(label, place['id'])
            res.append(place)

        return res


def preprocessor(text, *args):
    """
    >>> preprocessor('Ulko-Tammio')
    'paikka Ulko-Tammio'
    >>> preprocessor('Yli-Tapiola')
    'paikka Yli-Tapiola'
    >>> preprocessor('Helsinki-Vantaa')
    'paikka Helsinki Vantaa'
    >>> preprocessor('Oinola')
    'paikka Oinaala'
    >>> preprocessor('Helsinki,Oulu')
    'paikka Helsinki, Oulu'
    >>> preprocessor('Some text Helsinki')
    'paikka Some text Helsinki'
    >>> preprocessor('Sommeesta')
    'paikka Sommee'
    >>> preprocessor('Pidettiin Bio Rexissä')
    'paikka Pidettiin Helsinki'
    """

    text = text.replace('Yli-Tornio', 'Ylitornio')
    text = re.sub('Oin[ao]la', 'Oinaala', text)
    # Remove unit numbers that would otherwise be interpreted as Ii.
    text = re.sub('II(I)*', '', text)
    # Remove parentheses.
    text = re.sub('[()]', ' ', text)
    # Add a space after commas if they're followed by a word
    text = re.sub(r'(\w),(\w)', r'\1, \2', text)
    # Baseforming doesn't work for "Sommee" and "Muolaa" so baseform them manually.
    text = re.sub(r'Sommee(n?|s[st]a)?\b', 'Sommee', text)
    text = re.sub(r'Muolaa(n?|s[st]a)?\b', 'Muolaa', text)

    text = re.sub(r'Koivusiltaan', 'Koivusilta', text)

    text = re.sub(r'Raattee(n|s[st]a|lla)\b', 'Raate', text)
    text = re.sub(r'Summa(n|s[st]a|an)\b', 'Summa', text)

    text = re.sub(r'(Kannaksen|Aunuksen|Karjalan)\s+([Rr]yhmä|[Aa]rmeija)[a-zäö]*', '', text)

    # Karjalankannas is not handled properly by LAS
    text = re.sub(r'Karjalan\s*[Kk]kanna(s|ksen|ksell[ae]|sta)\b', 'Karjalankannas', text)
    text = re.sub(r'(Itä-|Länsi-|Keski-)?(?<!än )(?<![mstv]en )Kanna(s|ksen|ksell[ae]|sta)\b', 'Karjalankannas', text)

    text = re.sub(r'Repolasta', 'Repola', text)
    text = re.sub(r'Bio Rex(in|iss[aä])?', 'Helsinki', text)

    text = re.sub(r'Oravi(ssa|sta|in)', 'Oravi', text)

    text = re.sub(r'Saimaan [Kk]anava', 'Saimaankanava', text)
    # Detach names connected by hyphens to match places better.
    # Skip Yl[äi]-, Al[ia]-, Iso-, Ulko-, and Pitkä-
    text = re.sub(r'(?<!\b(Yl[äi]|Al[ia]|Iso))(?<!\bUlko)(?<!\bPitkä)-([A-ZÄÅÖ])', r' \2', text)

    text = text.replace('Inkilän kartano', '#')
    text = text.replace('Norjan Kirkkoniem', '#')
    text = text.replace('Pietari Autti', '#')

    # Too many places are interpreted as common nouns when they are the first
    # word in a sentence, so just prepend a word to the text to counteract this.

    text = text.replace('. ', '. paikka ')
    text = 'paikka ' + text

    text = text.strip()
    text = re.sub(r'\s+', ' ', text)

    return text


nen_re = re.compile(r'\w+nen\b')


def pruner(text):
    """
    >>> pruner('möttönen')
    >>> pruner('Saimaankanava')
    'Saimaankanava'
    >>> pruner('Tero Teronen')
    'Tero Teronen'
    >>> pruner('Tenenko')
    'Tenenko'
    >>> pruner('Tenenko Kaivo')
    'Tenenko Kaivo'
    >>> pruner('Tenengon kaivo')
    'Tenengon kaivo'
    >>> pruner('tenengon kaivo')
    >>> pruner('Lahdenpohja')
    'Lahdenpohja'
    """
    if not text[0].isupper():
        return None
    # if nen_re.search(text):
        # return None
    return text


if __name__ == '__main__':
    if sys.argv[1] == 'test':
        import doctest
        doctest.testmod()
        exit()

    ignore = [
        'sillanpää',
        'ritva',
        'pellonpää',
        'pajakoski',
        'kanto',
        'talvitie',
        'narva',
        'keskimaa',
        'kisko',
        'saari',
        'p',
        'm',
        's',
        'pohjoinen',
        'tienhaara',
        'suomalainen',
        'venäläinen',
        'asema',
        'ns',
        'rajavartiosto',
        'esikunta',
        'kauppa',
        'ryhmä',
        'ilma',
        'olla',
        'ruotsi',
        'pakkanen',
        'rannikko',
        'koulu',
        'kirkonkylä',
        'saksa',
        'työväentalo',
        'kirkko',
        'alku',
        'lentokenttä',
        'luoto',
        'risti',
        'posti',
        'lehti',
        'susi',
        'tykki',
        'prikaati',
        'niemi',
        'ranta',
        'eteläinen',
        'lappi',
        'järvi',
        'kallio',
        'salainen',
        'kannas',
        'taavetti',
        'berliini',
        'hannula',
        'hannuksela',
        'itä',
        'karhu',
        'tausta',
        'korkea',
        'niska',
        'saha',
        'komi',
        'aho',
        'kantti',
        'martola',
        'rättö',
        'oiva',
        'harald',
        'honkanen',
        'koskimaa',
        'järvinen',
        'autti',
        'suokanta',
        'holsti',
        'mäkinen',
        'rahola',
        'viro',
        'hakkila',
        'frans',
        'haukiperä',
        'lauri',
        'kolla',
        'kekkonen',
        'kello',
        'kari',
        'nurmi',
        'tiainen',
        'läntinen',
        'pajala',
        'pajakka',
        'malm',
        'kolla',
        'hiidenmaa',
        'kyösti',
        'pohjola',
        'mauno',
        'pekkala',
        'kylä',
        'kirkonkylä, kaupunki',
        'vesimuodostuma',
        'maastokohde',
        'kunta',
        'kallela',
        'palojärvi',
        'olli',
        'motti',
        'valko',
        'martti',
        'ilmarinen',
        'härkä',
        'suokas',
        'mäkelä',
        'kotiranta',
        'korpela',
        'mutta',
        'hillilä',
        'lohko',
        'pajari',
        'hauta',
        'tiirikkala',
        'virkkunen',
        'honka',
        'tapio',
        'sihvo',
        'rinne',
        'eskola',
        'paukku',
        'kuikka',
        'lehto',
        'villamo',
        'setälä',
        'lehmus',
        'vaala',
        'mukkala',
        'anttila',
        'kivi',
        'venäjä',
        'rex',
        'tunturi',
        'tahko',
        'runko',
        'kauria',
        'hassinen',
        'kyyrö',
        'kurimo',
        'möttönen',
        'ryönä',
        'ruotsalo',
        'rakola',
        'seppä',
        'aittola',
        'suo',
        'hermola',
        'mattila',
        'kuuma',
        'attila',
        'karjalaiskylä',
        'laakso',
        'hevoshaka',
        'keihäs',
        'palava',
        'klemetti',
        'kero',
        'romu',
        'kalevala',
        'keskimmäinen',
        'pio',
        'kartano',
        'amerikka',
        'itämeri',
        'kaleva',
        'paasto',
        'vuokko',
        'suutari',
        'fossi',
        'fagernäs',
        'jyrkkä',
        'kypärä',
        'löytö',
        'pesu',
        'satama',
        'teppo',
        'halli',
        'kola',
        'orava',
        'puoliväli',
        'tarkka',
        'asemi',
        'kauko',
        'piste',
        'karjala',
        'mylly',
        'kolma',
        'sotku',
        'ruotsinsalmi',  # boat
        'riilahti',  # boat
        # 'maaselkä',  # the proper one does not exist yet
        # 'kalajoki'  # the proper one does not exist yet
        # 'karsikko'?
    ]

    events_only_ignore = [
        'turtola',
        'pajari',
        'kivimäki',
        'pello',
        'rauhaniemi',
        'hallakorpi',
        'kontula',
        'törmä',
        'näsi',
        'lohikoski',
        'huhtala',
        'siiri',
        'jurva',
        'kujala',
        'kurjenmäki',
        'hietala',
        'puhakka',
        'helppi',
        # 'lehtovaara',
        'mäkelä',
        'palho',
        'härmälä',
        'torkkeli',
        'jutila',
        'rasi',
        'sirkka',
        'levo',
        'polo',
        'putkinotko',
        'ristola',
        'harmaala',
        'jukola',
        'varstala',
        'rongas',
        'linnus',
        'louko',
        'ruohola',
        'holm',
        'hakola',
        'suomela',
        'kalaja',
        'kalpio',
        'hovila',
        'komppa',
        'suna',
        'turja',
        'kanerva',
    ]

    if sys.argv[1] == 'event':
        print('Handling as events')
        ignore = ignore + events_only_ignore
        pruner_fun = pruner
    elif sys.argv[1] == 'photo':
        print('Handling as photos')
        pruner_fun = None
    else:
        raise ValueError('Invalid dataset')

    args = sys.argv[0:1] + sys.argv[2:]

    no_duplicates = [
        'http://www.yso.fi/onto/suo/kunta',
        'http://ldf.fi/schema/warsa/Town',
        'http://ldf.fi/schema/warsa/Village',
        'http://ldf.fi/schema/warsa/Body_of_water',
        'http://ldf.fi/schema/warsa/Hypsographic_feature',
        'http://ldf.fi/pnr-schema#place_type_540',
        'http://ldf.fi/pnr-schema#place_type_550',
        'http://ldf.fi/pnr-schema#place_type_560',
        ISLAND_TYPE, # Selected islands
    ]

    prep = preprocessor
    if args[-1] == 'naive':
        prep = None
        ignore = None
        no_duplicates = None
        args.pop()

    process_stage(args, ignore=ignore, pruner=pruner_fun, validator_class=Validator,
            preprocessor=preprocessor, remove_duplicates=no_duplicates)
