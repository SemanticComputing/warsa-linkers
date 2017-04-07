import sys
import re
from rdflib import Graph, Literal, Namespace

SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
KATA = Namespace('http://ldf.fi/warsa/kata/')

if __name__ == '__main__':
    uri_re = re.compile(r'Kansa_Taisteli_(\d+_\d+_page\d+)\.tes.txt')
    files = sys.argv[1:]

    for path in files:
        with open(path) as f:
            volume = uri_re.search(path).group(1)
            text = f.read()
            paragraphs = [t for t in text.split('\n\n') if re.sub(r'\s+', '', t)]
            g = Graph()
            for i, t in enumerate(paragraphs):
                t = re.sub(r'-\s*\n', '', t).replace('\n', ' ')
                t = Literal(t)
                uri = KATA['{}_{}'.format(volume, i)]
                g.add((uri, SKOS.prefLabel, t))
            g.serialize('{}.ttl'.format(volume), format='turtle')
