import logging
import unittest
# import doctest
# import units
import os
import sys
from unittest import TestCase
from rdflib import Graph, URIRef

from .units import Validator, preprocessor, get_match_scores


def setUpModule():
    logging.disable(logging.CRITICAL)


def tearDownModule():
    logging.disable(logging.NOTSET)


class TestUnitDisambiguation(TestCase):

    def setUp(self):
        g = Graph()
        dire = os.path.dirname(os.path.realpath(__file__))
        f = os.path.join(dire, 'test_photo_person.ttl')
        g.parse(f, format='turtle')
        self.validator = Validator(g)

    def test_conflict_selection(self):
        props_cw = {
            'war': ['<http://ldf.fi/warsa/conflicts/ContinuationWar>'],
            'label': ['"III/KTR 11"']
        }
        props_ww = {
            'war': ['<http://ldf.fi/warsa/conflicts/WinterWar>'],
            'label': ['"III/KTR 11"']
        }
        unit_cw = {
            'properties': props_cw,
            'label': 'III/KTR 11',
            'id': 'http://ldf.fi/warsa/actors/actor_15034'
        }
        unit_ww = {
            'properties': props_ww,
            'label': 'III/KTR 11',
            'id': 'http://ldf.fi/warsa/actors/actor_15035'
        }
        results = [unit_cw, unit_ww]

        s = URIRef('http://ldf.fi/warsa/photographs/sakuva_1000')
        self.assertEqual(self.validator.validate(results, '', s), [unit_cw])

        s = URIRef('http://ldf.fi/warsa/photographs/sakuva_104726')
        self.assertEqual(self.validator.validate(results, '', s), [unit_ww])

    def test_cover_number(self):
        props_cover_year = {
            'war': ['<http://ldf.fi/warsa/conflicts/ContinuationWar>'],
            'label': ['"1940"']
        }
        unit_year = {
            'properties': props_cover_year,
            'label': '1940',
            'id': 'http://ldf.fi/warsa/actors/actor_15034'
        }
        props_cover = {
            'war': ['<http://ldf.fi/warsa/conflicts/ContinuationWar>'],
            'label': ['"3100"']
        }
        unit = {
            'properties': props_cover,
            'label': '3100',
            'id': 'http://ldf.fi/warsa/actors/actor_15035'
        }
        results = [unit_year, unit]

        s = URIRef('http://ldf.fi/warsa/photographs/sakuva_1000')
        self.assertEqual(self.validator.validate(results, '', s), [unit])

        results = [unit_year]
        self.assertEqual(self.validator.validate(results, '', s), [])

        props_cover['label'] = ['"1814"']
        unit['properties'] = props_cover
        unit['label'] = '1814'
        results = [unit]
        self.assertEqual(self.validator.validate(results, '', s), [unit])

        props_cover['label'] = ['"1816"']
        unit['properties'] = props_cover
        unit['label'] = '1816'
        results = [unit]
        self.assertEqual(self.validator.validate(results, '', s), [])

    def test_check_cover(self):
        self.assertFalse(self.validator.check_cover('1800', '1800'))
        self.assertFalse(self.validator.check_cover('2000', '2000'))
        self.assertFalse(self.validator.check_cover('2010', 'Noin 2010'))
        self.assertFalse(self.validator.check_cover('2010', 'noin 2010'))
        self.assertFalse(self.validator.check_cover('2010', 'n. 2010'))
        self.assertFalse(self.validator.check_cover('2010', 'n.2010'))
        self.assertFalse(self.validator.check_cover('3030', '3030 m'))
        self.assertFalse(self.validator.check_cover('3030', '3030 m.'))
        self.assertFalse(self.validator.check_cover('3030', '3030m.'))
        self.assertFalse(self.validator.check_cover('4050', '4050 mk'))
        self.assertFalse(self.validator.check_cover('4050', '4050 mk.'))
        self.assertFalse(self.validator.check_cover('4050', '4050 markkaa'))
        self.assertFalse(self.validator.check_cover('3030', '3030 meter'))
        self.assertFalse(self.validator.check_cover('3030', '3030 metristä'))
        self.assertFalse(self.validator.check_cover('3030', '3030-jotain'))
        self.assertFalse(self.validator.check_cover('3030', '3030 kpl'))
        self.assertFalse(self.validator.check_cover('3030', '3030 tonnia'))
        self.assertFalse(self.validator.check_cover('3030', '3030 m:stä'))
        self.assertTrue(self.validator.check_cover('3030', '3030'))
        self.assertTrue(self.validator.check_cover('3030', '3030:n auto'))
        self.assertTrue(self.validator.check_cover('3030', 'jotain 3030 auto'))
        self.assertTrue(self.validator.check_cover('3030', 'Os. 3030:n auto'))
        self.assertTrue(self.validator.check_cover('3030', ''))
        self.assertEqual(self.validator.check_cover('', ''), None)
        self.assertEqual(self.validator.check_cover('not a number', ''), None)

    def test_preprocessor(self):
        self.assertEqual(preprocessor("Klo 8.52 ilmahälytys Viipurissa ja klo 9 pommitus KLo:a vastaan."), '8.52 ilmahälytys Viipurissa ja 9 pommitus KLo vastaan.')
        self.assertEqual(preprocessor("7 div.komendörs"), '7. D komendörs')
        self.assertEqual(preprocessor("Tyk.K/JR22:n hyökkäyskaistaa."), 'TykK/JR 22 hyökkäyskaistaa.')
        self.assertEqual(preprocessor("1/JR 10:ssä."), '1./JR 10.')
        self.assertEqual(preprocessor("1/JR10:ssä."), '1./JR 10.')
        self.assertEqual(preprocessor("JP1:n radioasema"), 'JP 1 radioasema')
        self.assertEqual(preprocessor("2./I/15.Pr."), '2./I/15. Pr.')
        self.assertEqual(preprocessor("IV.AKE."), 'IV AKE.')
        self.assertEqual(preprocessor("7 AKE"), 'VII AKE')
        self.assertEqual(preprocessor("7. AKE"), 'VII AKE')
        self.assertEqual(preprocessor("7.AKE"), 'VII AKE')
        self.assertEqual(preprocessor("7AKE"), 'VII AKE')
        self.assertEqual(preprocessor("(1/12.Pr.)"), '(1/12. Pr.)')
        self.assertEqual(preprocessor("Tsto 3/2. DE aliupseerit."), 'Tsto 3/2. DE aliupseerit.')
        self.assertEqual(preprocessor("pistooli m/41."), 'pistooli m/41.')
        self.assertEqual(preprocessor("Raskas patteristo/14.D. Elo-syyskuu 1944."), 'Raskas patteristo/14. D. Elo-syyskuu 1944.')
        self.assertEqual(preprocessor("Kenraalimajuri E.J.Raappana seurueineen."), 'Kenraalimajuri E.J.Raappana seurueineen.')
        self.assertEqual(preprocessor("J.R.8. komentaja, ev. Antti"), 'JR 8. komentaja, ev. Antti')
        self.assertEqual(preprocessor("Harlu JP.I."), 'Harlu JP 1.')
        self.assertEqual(preprocessor("2/JR 9."), '2./JR 9.')
        self.assertEqual(preprocessor("2./JR 9."), '2./JR 9.')
        self.assertEqual(preprocessor("11/JR 9."), '11./JR 9.')
        self.assertEqual(preprocessor("Laat Rpr"), 'Laat.RPr.')
        self.assertEqual(preprocessor("Laat.RPr"), 'Laat.RPr.')
        self.assertEqual(preprocessor("Laat.RPr."), 'Laat.RPr.')
        self.assertEqual(preprocessor("Laatokan Rpr:n"), 'Laatokan rannikkoprikaati')
        self.assertEqual(preprocessor("Laat. R. Pr. Purjehduskausi"), 'Laat.RPr. Purjehduskausi')
        self.assertEqual(preprocessor("Kenttäsairaala 35: Shakkia pelataan"), '35. Kenttäsairaala Shakkia pelataan')
        self.assertEqual(preprocessor("Kenttäsairaala A26. Valkotakkinen lääkäri"), '26. Kenttäsairaala. Valkotakkinen lääkäri')
        self.assertEqual(preprocessor("25.KS Os."), '25. KS Os.')
        self.assertEqual(preprocessor("KS 32"), '32. KS')
        self.assertEqual(preprocessor("14:sta LLv"), 'LLv 14 # LeLv 14')
        self.assertEqual(preprocessor("LLv.14"), 'LLv 14 # LeLv 14')
        self.assertEqual(preprocessor("Llv.14:n"), 'LLv 14 # LeLv 14')
        self.assertEqual(preprocessor("32llv"), 'LLv 32 # LeLv 32')
        self.assertEqual(preprocessor("I/JR II"), 'I/JR 2')
        self.assertEqual(preprocessor("8./JR II"), '8./JR 2')
        self.assertEqual(preprocessor("JR II"), 'JR 2')
        self.assertEqual(preprocessor("JR IV"), 'JR 4')
        self.assertEqual(preprocessor("Nyhamn´in linnakkeen"), 'Nyhamnin linnakkeen')
        self.assertEqual(preprocessor("JR 50´s avresa"), 'JR 50 avresa')
        self.assertEqual(preprocessor("II/ JR 50"), 'II/JR 50')

    def test_get_match_scores(self):
        props = {
            'war': ['<http://ldf.fi/warsa/conflicts/WinterWar>'],
            'label': ['"III/KTR 11"']
        }
        unit = {'properties': props, 'matches': ['III/KTR 11'], 'id': 'long'}
        props = {
            'war': ['<http://ldf.fi/warsa/conflicts/WinterWar>'],
            'label': ['"KTR 11"']
        }
        unit2 = {'properties': props, 'matches': ['KTR 11'], 'id': 'short'}
        results = [unit, unit2]

        res = get_match_scores(results)

        self.assertEqual(res['short'], False)
        self.assertEqual(res['long'], True)


if __name__ == '__main__':
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestUnitDisambiguation))
    # test_suite.addTest(doctest.DocTestSuite(units))
    unittest.TextTestRunner().run(test_suite)
