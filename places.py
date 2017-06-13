import re
import sys
from arpa_linker.link_helper import process_stage


class Validator:
    def __init__(self, graph, *args, **kwargs):
        self.graph = graph

    def validate(self, results, text, s):
        if not results:
            return results
        for i, place in enumerate(results):
            label = place.get('label')
            if label == "Rautalahti":
                results[i]['id'] = 'http://ldf.fi/warsa/places/karelian_places/k_place_33031'
            elif label == "Murtovaara":
                results[i]['id'] = 'http://ldf.fi/pnr/P_10558843'
            elif label == "Saarijärvi":
                results[i]['id'] = 'http://ldf.fi/warsa/places/karelian_places/k_place_37458'
            elif label == "Myllykoski":
                results[i]['id'] = 'http://ldf.fi/pnr/P_10130817'
            elif label == "Kuosmala":
                results[i]['id'] = 'http://ldf.fi/pnr/P_10392668'
            elif label == "Tyrävaara":
                results[i]['id'] = 'http://ldf.fi/pnr/P_10213175'
            elif label == "Kivivaara":
                results[i]['id'] = 'http://ldf.fi/pnr/P_10543550'
            elif "Lieks" in text and label == "Nurmijärvi":
                results[i]['id'] = 'http://ldf.fi/pnr/P_10588451'
            elif label == "Kotka":
                results[i]['id'] = 'http://ldf.fi/pnr/P_10878654'
            elif label == "Malmi":
                results[i]['id'] = 'http://ldf.fi/pnr/P_10012991'
            elif label == "Kylänmäki":
                results[i]['id'] = 'http://ldf.fi/pnr/P_10530797'
            elif label == "Käpylä":
                results[i]['id'] = 'http://ldf.fi/pnr/P_10342681'

        return results


def preprocessor(text, *args):
    """
    >>> preprocessor('Ulko-Tammio')
    'Ulko-Tammio'
    >>> preprocessor('Yli-Tapiola')
    'Yli-Tapiola'
    >>> preprocessor('Helsinki-Vantaa')
    'Helsinki Vantaa'
    >>> preprocessor('Oinola')
    'Oinaala'
    >>> preprocessor('Helsinki,Oulu')
    'Helsinki, Oulu'
    >>> preprocessor('Some text Helsinki')
    'Some text Helsinki'
    >>> preprocessor('Sommeesta')
    'Sommee'
    >>> preprocessor('Pidettiin Bio Rexissä')
    'Pidettiin Helsinki'
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

    text = re.sub(r'Helsingi(n?|s[st]ä)\b', 'Helsinki', text)
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

    text = text.strip()
    text = re.sub(r'\s+', ' ', text)

    return text


nen_re = re.compile(r'\w+nen\b')


def pruner(text):
    """
    >>> pruner('Möttönen')
    >>> pruner('Saimaankanava')
    'Saimaankanava'
    >>> pruner('Tero Teronen')
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
    if nen_re.search(text):
        return None
    return text


if __name__ == '__main__':
    if sys.argv[1] == 'test':
        import doctest
        doctest.testmod()
        exit()

    ignore = [
        'sillanpää',
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
        'lehtovaara',
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
    ]

    prep = preprocessor
    if args[-1] == 'naive':
        prep = None
        ignore = None
        no_duplicates = None
        args.pop()

    process_stage(args, ignore=ignore, pruner=pruner_fun, validator_class=Validator,
            preprocessor=preprocessor, remove_duplicates=no_duplicates)
