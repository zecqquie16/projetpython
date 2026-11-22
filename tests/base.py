import unittest

from Corpus import Corpus


class TestAvecCorpusVierge(unittest.TestCase):
    """Base des tests qui utilisent Corpus.

    Corpus est un Singleton : sans précaution, tous les tests se partageraient le
    même corpus et les documents d'un test fuiraient dans le suivant. On oublie
    donc l'instance avant chaque test, et une dernière fois à la fin.
    """

    def setUp(self):
        Corpus.reinitialiser()
        self.addCleanup(Corpus.reinitialiser)
