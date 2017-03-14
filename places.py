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

        return results


def preprocessor(text, *args):
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
    # Detach names connected by hyphens to match places better.
    # Skip Yl[äi]-, Al[ia]-, Iso-. and Pitkä-
    text = text.replace('Pitkä-', 'Pitkä#')
    text = re.sub(r'(?<!\b(Yl[äi]|Al[ia]|Iso))-([A-ZÄÅÖ])', r' \2', text)
    text = text.replace('Pitkä#', 'Pitkä-')

    text = text.replace('Inkilän kartano', '#')
    text = text.replace('Norjan Kirkkoniem', '#')
    text = text.replace('Pietari Autti', '#')

    text = text.strip()
    text = re.sub(r'\s+', ' ', text)

    return text

if __name__ == '__main__':

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
        # 'maaselkä',  # the proper one does not exist yet
        # 'kalajoki'  # the proper one does not exist yet
        # 'karsikko'?
    ]

    events_only_ignore = [
        'turtola',
        'pajari',
        'kivimäki'
    ]

    if sys.argv[1] == 'event':
        print('Handling as events')
        ignore = ignore + events_only_ignore
    elif sys.argv[1] == 'photo':
        print('Handling as photos')
    else:
        raise ValueError('Invalid dataset')

    args = sys.argv[0:1] + sys.argv[2:]

    no_duplicates = [
        'http://www.yso.fi/onto/suo/kunta',
        'http://ldf.fi/warsa/places/place_types/Kirkonkyla_kaupunki',
        'http://ldf.fi/warsa/places/place_types/Kyla',
        'http://ldf.fi/warsa/places/place_types/Vesimuodostuma',
        'http://ldf.fi/warsa/places/place_types/Maastokohde',
        'http://ldf.fi/pnr-schema#place_type_540',
        'http://ldf.fi/pnr-schema#place_type_550',
        'http://ldf.fi/pnr-schema#place_type_560',
    ]

    process_stage(args, ignore=ignore, validator_class=Validator,
            preprocessor=preprocessor, remove_duplicates=no_duplicates)
