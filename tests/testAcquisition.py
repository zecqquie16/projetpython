"""Tests de l'acquisition (analyse des réponses des APIs) et du branchement dans main.py.

Aucun test n'accède à Internet : les réponses des APIs sont simulées.
"""

import contextlib
import io
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import main
from Acquisition import _parser_arxiv, _parser_hn
from Corpus import Corpus
from Document import Document
from tests.base import TestAvecCorpusVierge

REPONSE_HN = {
    "hits": [
        {   # post avec texte : balises <p> et entités HTML à nettoyer, pas d'url externe
            "title": "Post avec texte", "story_text": "Bonjour<p>le monde &#x27;ok&#x27;",
            "author": "alice", "created_at": "2020-03-11T10:20:30.000Z",
            "url": None, "objectID": "111",
        },
        {   # post avec lien seulement : pas de story_text, on se rabat sur le titre
            "title": "Post avec lien", "author": "bob",
            "created_at": "2020-03-12T08:00:00.000Z",
            "url": "https://exemple.org", "objectID": "222",
        },
        {   # champs manquants : ne doit pas faire planter
            "title": None, "author": None, "objectID": "333",
        },
    ]
}

ENTREE_ARXIV = (
    "<entry><id>http://arxiv.org/abs/1</id><published>2020-03-01T12:00:00Z</published>"
    "<title>Titre sur\ndeux lignes</title><summary>Résumé\navec un saut.</summary>"
    "{auteurs}</entry>"
)
UN_AUTEUR = "<author><name>Alice A</name></author>"
DEUX_AUTEURS = "<author><name>Alice A</name></author><author><name>Bob B</name></author>"


def xml_arxiv(*entrees):
    return ("<?xml version='1.0' encoding='UTF-8'?>"
            "<feed xmlns='http://www.w3.org/2005/Atom'>" + "".join(entrees) + "</feed>")


class TestParserHackerNews(unittest.TestCase):
    def setUp(self):
        self.docs = _parser_hn(REPONSE_HN)

    def test_nombre_de_documents(self):
        self.assertEqual(len(self.docs), 3)

    def test_nettoyage_html(self):
        self.assertEqual(self.docs[0]["texte"], "Bonjour le monde 'ok'")

    def test_repli_sur_le_titre_sans_story_text(self):
        self.assertEqual(self.docs[1]["texte"], "Post avec lien")

    def test_url_de_repli_vers_la_page_hacker_news(self):
        self.assertEqual(self.docs[0]["url"], "https://news.ycombinator.com/item?id=111")
        self.assertEqual(self.docs[1]["url"], "https://exemple.org")

    def test_champs_manquants_ne_plantent_pas(self):
        manquant = self.docs[2]
        self.assertEqual(manquant["auteur"], "inconnu")
        self.assertEqual(manquant["titre"], "")
        self.assertIsNone(manquant["date"])

    def test_reponse_vide(self):
        self.assertEqual(_parser_hn({"hits": []}), [])
        self.assertEqual(_parser_hn({}), [])


class TestParserArxiv(unittest.TestCase):
    def test_un_seul_resultat_ne_plante_pas(self):
        # xmltodict renvoie un dict (pas une liste) dans ce cas
        docs = _parser_arxiv(xml_arxiv(ENTREE_ARXIV.format(auteurs=UN_AUTEUR)))
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["auteur"], "Alice A")
        self.assertEqual(docs[0]["url"], "http://arxiv.org/abs/1")
        self.assertEqual(docs[0]["date"], "2020-03-01T12:00:00Z")

    def test_plusieurs_resultats(self):
        xml = xml_arxiv(ENTREE_ARXIV.format(auteurs=UN_AUTEUR),
                        ENTREE_ARXIV.format(auteurs=UN_AUTEUR))
        self.assertEqual(len(_parser_arxiv(xml)), 2)

    def test_plusieurs_auteurs_on_garde_le_premier(self):
        docs = _parser_arxiv(xml_arxiv(ENTREE_ARXIV.format(auteurs=DEUX_AUTEURS)))
        self.assertEqual(docs[0]["auteur"], "Alice A")

    def test_sans_auteur(self):
        docs = _parser_arxiv(xml_arxiv(ENTREE_ARXIV.format(auteurs="")))
        self.assertEqual(docs[0]["auteur"], "inconnu")

    def test_sauts_de_ligne_supprimes(self):
        docs = _parser_arxiv(xml_arxiv(ENTREE_ARXIV.format(auteurs=UN_AUTEUR)))
        self.assertEqual(docs[0]["titre"], "Titre sur deux lignes")
        self.assertEqual(docs[0]["texte"], "Résumé avec un saut.")

    def test_aucun_resultat(self):
        self.assertEqual(_parser_arxiv(xml_arxiv()), [])
        self.assertEqual(_parser_arxiv("<feed/>"), [])


def un_doc(titre, auteur, texte="Un texte assez long pour passer le filtre."):
    return {"type_doc": "Hacker News", "titre": titre, "auteur": auteur,
            "date": "2020-01-01T00:00:00Z", "url": "http://x", "texte": texte}


def silencieux():
    """Capture ce que le programme affiche, pour garder la sortie des tests propre."""
    return contextlib.redirect_stdout(io.StringIO())


class TestConstruireCorpus(TestAvecCorpusVierge):
    def test_documents_des_deux_sources(self):
        hn = [un_doc("A", "alice"), un_doc("B", "bob")]
        arxiv = [un_doc("C", "alice")]
        with mock.patch("main.fetch_hackernews", return_value=hn), \
                mock.patch("main.fetch_arxiv", return_value=arxiv), silencieux():
            corpus = main.construire_corpus("test", 10)
        self.assertEqual(corpus.ndoc, 3)
        self.assertEqual(corpus.naut, 2)  # alice n'est comptée qu'une fois

    def test_textes_trop_courts_ecartes(self):
        hn = [un_doc("Court", "alice", texte="trop court"), un_doc("Long", "alice")]
        with mock.patch("main.fetch_hackernews", return_value=hn), \
                mock.patch("main.fetch_arxiv", return_value=[]), silencieux():
            corpus = main.construire_corpus("test", 10)
        self.assertEqual(corpus.ndoc, 1)

    def test_une_source_en_panne_ne_fait_pas_planter(self):
        arxiv = [un_doc("C", "alice")]
        with mock.patch("main.fetch_hackernews", side_effect=urllib.error.URLError("hors ligne")), \
                mock.patch("main.fetch_arxiv", return_value=arxiv), silencieux():
            corpus = main.construire_corpus("test", 10)
        self.assertEqual(corpus.ndoc, 1)

    def test_deux_sources_en_panne(self):
        with mock.patch("main.fetch_hackernews", side_effect=TimeoutError()), \
                mock.patch("main.fetch_arxiv", side_effect=ValueError("XML invalide")), silencieux():
            corpus = main.construire_corpus("test", 10)
        self.assertEqual(corpus.ndoc, 0)


class TestChargerOuConstruire(TestAvecCorpusVierge):
    def test_csv_absent_acquisition_puis_sauvegarde(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "data" / "corpus.csv"
            hn = [un_doc("A", "alice")]
            with mock.patch.object(main, "CHEMIN_CSV", chemin), \
                    mock.patch("main.fetch_hackernews", return_value=hn), \
                    mock.patch("main.fetch_arxiv", return_value=[]), silencieux():
                corpus = main.charger_ou_construire()
            self.assertEqual(corpus.ndoc, 1)
            self.assertTrue(chemin.exists())

    def test_csv_present_aucun_appel_aux_apis(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "corpus.csv"
            sauvegarde = Corpus("x")
            sauvegarde.add_document(Document("T", "alice", "2020-01-01T00:00:00Z", "http://x", "texte"))
            sauvegarde.save(chemin)
            with mock.patch.object(main, "CHEMIN_CSV", chemin), \
                    mock.patch("main.fetch_hackernews") as hn, \
                    mock.patch("main.fetch_arxiv") as arxiv, silencieux():
                corpus = main.charger_ou_construire()
            hn.assert_not_called()
            arxiv.assert_not_called()
            self.assertEqual(corpus.ndoc, 1)

    def test_csv_au_format_td3_on_repart_des_apis(self):
        # Le CSV du TD3 a les colonnes id / texts / org, pas celles du Corpus
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "corpus.csv"
            chemin.write_text("id\ttexts\torg\n0\tbonjour le monde\thackernews\n", encoding="utf-8")
            with mock.patch.object(main, "CHEMIN_CSV", chemin), \
                    mock.patch("main.fetch_hackernews", return_value=[un_doc("A", "alice")]), \
                    mock.patch("main.fetch_arxiv", return_value=[]), silencieux():
                corpus = main.charger_ou_construire()
            self.assertEqual(corpus.ndoc, 1)

    def test_aucun_document_rien_n_est_sauvegarde(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "corpus.csv"
            with mock.patch.object(main, "CHEMIN_CSV", chemin), \
                    mock.patch("main.fetch_hackernews", return_value=[]), \
                    mock.patch("main.fetch_arxiv", return_value=[]), silencieux():
                corpus = main.charger_ou_construire()
            self.assertEqual(corpus.ndoc, 0)
            self.assertFalse(chemin.exists())


class TestMenuAuteur(TestAvecCorpusVierge):
    def creer_corpus(self):
        corpus = Corpus("test")
        corpus.add_document(Document("A", "Alice", "2020-01-01T00:00:00Z", "http://a", "1234"))
        corpus.add_document(Document("B", "Alice", "2020-01-02T00:00:00Z", "http://b", "12"))
        return corpus

    def test_stats_de_l_auteur_saisi(self):
        sortie = io.StringIO()
        with mock.patch("builtins.input", side_effect=["Alice", ""]), \
                contextlib.redirect_stdout(sortie):
            main.menu_stats_auteur(self.creer_corpus())
        self.assertIn("Alice : 2 document(s), taille moyenne 3 caractères", sortie.getvalue())

    def test_auteur_inconnu(self):
        sortie = io.StringIO()
        with mock.patch("builtins.input", side_effect=["Zorro", ""]), \
                contextlib.redirect_stdout(sortie):
            main.menu_stats_auteur(self.creer_corpus())
        self.assertIn("Auteur inconnu : Zorro", sortie.getvalue())

    def test_sans_clavier_ne_plante_pas(self):
        with mock.patch("builtins.input", side_effect=EOFError), silencieux():
            main.menu_stats_auteur(self.creer_corpus())


if __name__ == "__main__":
    unittest.main()