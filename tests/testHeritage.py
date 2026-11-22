"""Tests de l'héritage (classes filles) et de leur utilisation dans le Corpus (TD5, parties 1 à 3)."""

import contextlib
import io
import unittest

from Acquisition import _parser_arxiv, _parser_hn
from Corpus import Corpus
from Document import ArxivDocument, Document, HackerNewsDocument
from tests.base import TestAvecCorpusVierge


def sortie_de(fonction, *args, **kwargs):
    """Retourne les lignes affichées par fonction(*args, **kwargs)."""
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        fonction(*args, **kwargs)
    return tampon.getvalue().splitlines()


def doc_hn(titre="Post HN", auteur="alice", nb=12, date="2021-05-01T10:00:00Z"):
    return HackerNewsDocument(titre, auteur, date, "http://hn", "texte hn", nb)


def doc_arxiv(titre="Article Arxiv", auteur="Bob B", co_auteurs=("Carol C", "Dan D"),
              date="2022-01-01T10:00:00Z"):
    return ArxivDocument(titre, auteur, date, "http://arxiv", "texte arxiv", co_auteurs)


class TestHackerNewsDocument(unittest.TestCase):
    def test_herite_de_document(self):
        self.assertIsInstance(doc_hn(), Document)

    def test_constructeur_appelle_celui_de_la_classe_mere(self):
        doc = doc_hn(titre="T", auteur="alice", date="2021-05-01T10:00:00Z")
        self.assertEqual((doc.titre, doc.auteur, doc.url, doc.texte), ("T", "alice", "http://hn", "texte hn"))
        self.assertEqual(doc.date.year, 2021)  # conversion de la date faite par Document

    def test_accesseur_et_mutateur(self):
        doc = doc_hn(nb=12)
        self.assertEqual(doc.get_nb_commentaires(), 12)
        doc.set_nb_commentaires(30)
        self.assertEqual(doc.get_nb_commentaires(), 30)

    def test_str_utilise_le_nombre_de_commentaires(self):
        self.assertEqual(str(doc_hn(titre="Mon post", nb=12)), "Mon post (12 commentaires)")

    def test_type(self):
        self.assertEqual(doc_hn().getType(), "Hacker News")

    def test_valeur_par_defaut_du_nombre_de_commentaires(self):
        doc = HackerNewsDocument("T", "a", None, "u", "x")
        self.assertEqual(doc.get_nb_commentaires(), 0)


class TestArxivDocument(unittest.TestCase):
    def test_herite_de_document(self):
        self.assertIsInstance(doc_arxiv(), Document)

    def test_accesseur_et_mutateur(self):
        doc = doc_arxiv()
        self.assertEqual(doc.get_co_auteurs(), ["Carol C", "Dan D"])
        doc.set_co_auteurs(["Eve E"])
        self.assertEqual(doc.get_co_auteurs(), ["Eve E"])

    def test_add_co_auteur_sans_doublon(self):
        doc = doc_arxiv(co_auteurs=["Carol C"])
        doc.add_co_auteur("Dan D")
        doc.add_co_auteur("Carol C")  # déjà présent : ignoré
        self.assertEqual(doc.get_co_auteurs(), ["Carol C", "Dan D"])

    def test_la_liste_est_copiee(self):
        liste = ["Carol C"]
        doc = doc_arxiv(co_auteurs=liste)
        liste.append("Intrus")  # ne doit pas modifier le document
        self.assertEqual(doc.get_co_auteurs(), ["Carol C"])

    def test_str_utilise_les_co_auteurs(self):
        doc = doc_arxiv(titre="Mon article")
        self.assertEqual(str(doc), "Mon article (Co-auteurs : Carol C, Dan D)")

    def test_type(self):
        self.assertEqual(doc_arxiv().getType(), "Arxiv")


class TestTypeDansLaClasseMere(unittest.TestCase):
    def test_document_simple(self):
        self.assertEqual(Document("T", "a", None, "u", "x").getType(), "Document")

    def test_champ_type_present(self):
        self.assertEqual(doc_hn().type, "Hacker News")
        self.assertEqual(doc_arxiv().type, "Arxiv")


class TestPolymorphismeDansLeCorpus(TestAvecCorpusVierge):
    """TD5 3.1 : le Corpus accepte les deux classes filles sans avoir été modifié."""

    def setUp(self):
        super().setUp()
        self.corpus = Corpus("test")
        self.corpus.add_document(doc_hn("Post A", "alice", date="2021-05-01T10:00:00Z"))
        self.corpus.add_document(doc_arxiv("Article B", "Bob B", date="2022-01-01T10:00:00Z"))
        self.corpus.add_document(doc_hn("Post C", "alice", date="2020-01-01T10:00:00Z"))

    def test_compteurs(self):
        self.assertEqual(self.corpus.ndoc, 3)
        self.assertEqual(self.corpus.naut, 2)  # alice n'est comptée qu'une fois

    def test_production_de_l_auteur(self):
        self.assertEqual(self.corpus.authors["alice"].ndoc, 2)

    def test_les_objets_gardent_leur_classe(self):
        self.assertIsInstance(self.corpus.id2doc[0], HackerNewsDocument)
        self.assertIsInstance(self.corpus.id2doc[1], ArxivDocument)

    def test_tris_existants_fonctionnent_avec_les_classes_filles(self):
        par_date = sortie_de(self.corpus.afficher_par_date, 3)
        self.assertEqual([l.split(" | ")[1] for l in par_date], ["Article B", "Post A", "Post C"])
        par_titre = sortie_de(self.corpus.afficher_par_titre, 3)
        self.assertEqual([l.split(" | ")[0] for l in par_titre], ["Article B", "Post A", "Post C"])

    def test_stats_auteur(self):
        lignes = sortie_de(self.corpus.stats_auteur, "alice")
        self.assertEqual(len(lignes), 1)
        self.assertIn("alice : 2 document(s)", lignes[0])


class TestAffichageAvecLaSource(TestAvecCorpusVierge):
    """TD5 3.2 : afficher les documents avec leur source."""

    def setUp(self):
        super().setUp()
        self.corpus = Corpus("test")
        self.corpus.add_document(doc_hn("Post A", nb=7))
        self.corpus.add_document(doc_arxiv("Article B", co_auteurs=["Carol C"]))
        self.corpus.add_document(Document("Doc simple", "zoe", None, "u", "x"))

    def test_chaque_ligne_affiche_la_source_et_le_str_propre_a_la_classe(self):
        lignes = sortie_de(self.corpus.afficher_liste)
        self.assertEqual(lignes, [
            "  0 [Hacker News] Post A (7 commentaires)",
            "  1 [Arxiv] Article B (Co-auteurs : Carol C)",
            "  2 [Document] Doc simple",
        ])

    def test_limite_n(self):
        self.assertEqual(len(sortie_de(self.corpus.afficher_liste, 2)), 2)

    def test_filtre_par_source(self):
        lignes = sortie_de(self.corpus.afficher_liste, None, "Arxiv")
        self.assertEqual(lignes, ["  1 [Arxiv] Article B (Co-auteurs : Carol C)"])

    def test_sources_presentes(self):
        self.assertEqual(self.corpus.sources(), ["Arxiv", "Document", "Hacker News"])

    def test_corpus_vide(self):
        Corpus.reinitialiser()
        vide = Corpus("vide")
        self.assertEqual(sortie_de(vide.afficher_liste), [])
        self.assertEqual(vide.sources(), [])


class TestAcquisitionTypee(unittest.TestCase):
    """Les parsers fournissent les champs propres à chaque source."""

    def test_hacker_news_nombre_de_commentaires(self):
        docs = _parser_hn({"hits": [
            {"title": "A", "num_comments": 42, "objectID": "1"},
            {"title": "B", "num_comments": None, "objectID": "2"},
            {"title": "C", "objectID": "3"},
        ]})
        self.assertEqual([d["nb_commentaires"] for d in docs], [42, 0, 0])
        self.assertEqual({d["type_doc"] for d in docs}, {"Hacker News"})

    def test_arxiv_co_auteurs(self):
        xml = ("<feed xmlns='http://www.w3.org/2005/Atom'><entry><id>http://a</id>"
               "<title>T</title><summary>S</summary>"
               "<author><name>Alice A</name></author><author><name>Bob B</name></author>"
               "<author><name>Carol C</name></author></entry></feed>")
        doc = _parser_arxiv(xml)[0]
        self.assertEqual(doc["auteur"], "Alice A")
        self.assertEqual(doc["co_auteurs"], ["Bob B", "Carol C"])
        self.assertEqual(doc["type_doc"], "Arxiv")

    def test_arxiv_un_seul_auteur_aucun_co_auteur(self):
        xml = ("<feed xmlns='http://www.w3.org/2005/Atom'><entry><id>http://a</id>"
               "<title>T</title><summary>S</summary>"
               "<author><name>Alice A</name></author></entry></feed>")
        self.assertEqual(_parser_arxiv(xml)[0]["co_auteurs"], [])


if __name__ == "__main__":
    unittest.main()
