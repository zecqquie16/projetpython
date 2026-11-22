"""Tests de Document (conversion des dates) et des affichages triés / stats du Corpus."""

import contextlib
import io
import unittest
from datetime import datetime, timedelta, timezone

from Corpus import Corpus
from Document import Document, convertir_date
from tests.base import TestAvecCorpusVierge


def sortie_de(fonction, *args):
    """Retourne les lignes affichées par fonction(*args)."""
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        fonction(*args)
    return tampon.getvalue().splitlines()


class TestConvertirDate(unittest.TestCase):
    def test_format_iso_avec_z(self):
        self.assertEqual(convertir_date("2024-03-01T10:00:00Z"), datetime(2024, 3, 1, 10, 0, 0))

    def test_format_hacker_news_avec_millisecondes(self):
        self.assertEqual(convertir_date("2020-03-11T10:20:30.000Z"), datetime(2020, 3, 11, 10, 20, 30))

    def test_datetime_avec_fuseau_devient_naif(self):
        avec_fuseau = datetime(2024, 3, 1, 10, 0, 0, tzinfo=timezone(timedelta(hours=1)))
        self.assertIsNone(convertir_date(avec_fuseau).tzinfo)

    def test_dates_invalides_ou_absentes(self):
        self.assertIsNone(convertir_date(None))
        self.assertIsNone(convertir_date(""))
        self.assertIsNone(convertir_date("pas une date"))


class TestDocument(unittest.TestCase):
    def test_str_renvoie_le_titre(self):
        doc = Document("Mon titre", "alice", "2024-03-01T10:00:00Z", "http://x", "texte")
        self.assertEqual(str(doc), "Mon titre")


class TestAffichagesCorpus(TestAvecCorpusVierge):
    def setUp(self):
        super().setUp()
        self.corpus = Corpus("test")
        self.corpus.add_document(Document("banana", "Alice", "2024-01-01T00:00:00Z", "http://1", "aaaa"))
        self.corpus.add_document(Document("Apple", "Bob", "2024-03-01T00:00:00Z", "http://2", "bb"))
        self.corpus.add_document(Document("cherry", "Alice", None, "http://3", "cccccc"))

    def test_par_date_du_plus_recent_au_plus_ancien(self):
        lignes = sortie_de(self.corpus.afficher_par_date, 3)
        self.assertEqual([l.split(" | ")[1] for l in lignes], ["Apple", "banana", "cherry"])

    def test_par_date_limite_n(self):
        self.assertEqual(len(sortie_de(self.corpus.afficher_par_date, 2)), 2)

    def test_par_titre_ordre_alphabetique_sans_tenir_compte_des_majuscules(self):
        lignes = sortie_de(self.corpus.afficher_par_titre, 3)
        self.assertEqual([l.split(" | ")[0] for l in lignes], ["Apple", "banana", "cherry"])

    def test_n_plus_grand_que_le_corpus(self):
        self.assertEqual(len(sortie_de(self.corpus.afficher_par_titre, 50)), 3)


class TestStatsAuteur(TestAvecCorpusVierge):
    def setUp(self):
        super().setUp()
        self.corpus = Corpus("test")
        self.corpus.add_document(Document("A", "Alice", "2024-01-01T00:00:00Z", "http://1", "1234"))
        self.corpus.add_document(Document("B", "Alice", "2024-01-02T00:00:00Z", "http://2", "12"))

    def test_auteur_connu(self):
        lignes = sortie_de(self.corpus.stats_auteur, "Alice")
        self.assertEqual(lignes, ["Alice : 2 document(s), taille moyenne 3 caractères"])

    def test_auteur_inconnu(self):
        self.assertEqual(sortie_de(self.corpus.stats_auteur, "Zorro"), ["Auteur inconnu : Zorro"])


if __name__ == "__main__":
    unittest.main()