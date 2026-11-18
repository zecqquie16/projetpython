import tempfile
import unittest
from pathlib import Path

from Corpus import Corpus
from Document import Document


def creer_corpus():
    corpus = Corpus("test")
    corpus.add_document(Document("Titre B", "Alice", "2024-03-01T10:00:00Z", "http://a", "1234"))
    corpus.add_document(Document("Titre A", "Bob", "2024-05-01T10:00:00Z", "http://b", "12345678"))
    corpus.add_document(Document("Titre C", "Alice", "2023-01-01T10:00:00Z", "http://c", "12"))
    return corpus


class TestCorpus(unittest.TestCase):
    def test_compteurs(self):
        corpus = creer_corpus()
        self.assertEqual(corpus.ndoc, 3)
        self.assertEqual(corpus.naut, 2)  # Alice n'est comptée qu'une fois

    def test_production_auteur(self):
        corpus = creer_corpus()
        self.assertEqual(corpus.authors["Alice"].ndoc, 2)

    def test_taille_moyenne(self):
        corpus = creer_corpus()
        self.assertEqual(corpus.authors["Alice"].taille_moyenne(), 3)  # (4 + 2) / 2

    def test_save_load(self):
        corpus = creer_corpus()
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "c.csv"
            corpus.save(chemin)
            recharge = Corpus.load(chemin)
        self.assertEqual(recharge.ndoc, corpus.ndoc)
        self.assertEqual(recharge.naut, corpus.naut)
        self.assertEqual(recharge.id2doc[1].titre, "Titre A")


if __name__ == "__main__":
    unittest.main()