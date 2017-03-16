import logging
import unittest
# import doctest
# import units
import os
import sys
from unittest import TestCase
from rdflib import Graph, URIRef

from units import Validator, preprocessor


def setUpModule():
    logging.disable(logging.CRITICAL)


def tearDownModule():
    logging.disable(logging.NOTSET)


class TestUnitDisambiguation(TestCase):

    def setUp(self):
        g = Graph()
        f = os.path.join(sys.path[0], 'test_photo_person.ttl')
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
        props_cover = {
            'war': ['<http://ldf.fi/warsa/conflicts/ContinuationWar>'],
            'label': ['"3000"']
        }
        unit_year = {
            'properties': props_cover_year,
            'label': '1940',
            'id': 'http://ldf.fi/warsa/actors/actor_15034'
        }
        unit = {
            'properties': props_cover,
            'label': '3000',
            'id': 'http://ldf.fi/warsa/actors/actor_15035'
        }
        results = [unit_year, unit]

        s = URIRef('http://ldf.fi/warsa/photographs/sakuva_1000')
        self.assertEqual(self.validator.validate(results, '', s), [unit])

        results = [unit_year]
        self.assertEqual(self.validator.validate(results, '', s), [])

    def test_preprocessor(self):
        self.assertEqual(preprocessor("Klo 8.52 ilmahälytys Viipurissa ja klo 9 pommitus Kotkan lohkoa vastaan."), 'klo 8.52 ilmahälytys Viipurissa ja klo 9 pommitus Kotkan lohkoa vastaan.')
        self.assertEqual(preprocessor("7 div.komendörs"), '7. D komendörs')
        self.assertEqual(preprocessor("Tyk.K/JR22:n hyökkäyskaistaa."), 'TykK/JR 22 hyökkäyskaistaa. # JR 22')
        self.assertEqual(preprocessor("1/JR 10:ssä."), 'I/JR 10. # JR 10')
        self.assertEqual(preprocessor("1/JR10:ssä."), 'I/JR 10. # JR 10')
        self.assertEqual(preprocessor("JP1:n radioasema"), 'JP 1 radioasema')
        self.assertEqual(preprocessor("2./I/15.Pr."), '2./I/15. Pr. # 15. Pr')
        self.assertEqual(preprocessor("IV.AKE."), 'IV AKE.')
        self.assertEqual(preprocessor("(1/12.Pr.)"), '(1/12. Pr.) # 12. Pr')
        self.assertEqual(preprocessor("Tsto 3/2. DE aliupseerit."), 'Tsto 3/2. DE aliupseerit. # 2. DE')
        self.assertEqual(preprocessor("pistooli m/41."), 'pistooli m/41.')
        self.assertEqual(preprocessor("Raskas patteristo/14.D. Elo-syyskuu 1944."), 'Raskas patteristo/14. D. Elo-syyskuu 1944. # 14. D')
        self.assertEqual(preprocessor("Kenraalimajuri E.J.Raappana seurueineen."), 'Kenraalimajuri E.J.Raappana seurueineen.')
        self.assertEqual(preprocessor("J.R.8. komentaja, ev. Antti"), 'JR 8. komentaja, ev. Antti')
        self.assertEqual(preprocessor("Harlu JP.I."), 'Harlu JP 1.')
        self.assertEqual(preprocessor("2/JR 9."), 'II/JR 9. # JR 9')
        self.assertEqual(preprocessor("2./JR 9."), 'II/JR 9. # JR 9')
        self.assertEqual(preprocessor("11/JR 9."), 'XI/JR 9. # JR 9')
        self.assertEqual(preprocessor("Laat Rpr"), 'Laat.RPr.')
        self.assertEqual(preprocessor("Laat.RPr"), 'Laat.RPr.')
        self.assertEqual(preprocessor("Laat.RPr."), 'Laat.RPr.')
        self.assertEqual(preprocessor("Laatokan Rpr:n"), 'Laatokan rannikkoprikaati')
        self.assertEqual(preprocessor("Laat. R. Pr. Purjehduskausi"), 'Laat.RPr. Purjehduskausi')
        self.assertEqual(preprocessor("Kenttäsairaala 35: Shakkia pelataan"), '35. Kenttäsairaala: Shakkia pelataan')
        self.assertEqual(preprocessor("Kenttäsairaala A26. Valkotakkinen lääkäri"), '26. Kenttäsairaala. Valkotakkinen lääkäri')
        self.assertEqual(preprocessor("25.KS Os."), '25. KS Os.')
        self.assertEqual(preprocessor("KS 32"), '32. KS')

if __name__ == '__main__':
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestUnitDisambiguation))
    # test_suite.addTest(doctest.DocTestSuite(units))
    unittest.TextTestRunner().run(test_suite)
