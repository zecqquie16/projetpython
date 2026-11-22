"""Tests des patrons de conception : Singleton et Factory (TD5, partie 4),
et de la sauvegarde / du rechargement des types de documents.
"""

import tempfile
import unittest
from pathlib import Path

from Corpus import Corpus
from Document import ArxivDocument, Document, HackerNewsDocument
from DocumentFactory import DocumentFactory
from Singleton import Singleton
from tests.base import TestAvecCorpusVierge


class TestSingleton(TestAvecCorpusVierge):
    def test_une_seule_instance(self):
        premier = Corpus("a")
        second = Corpus("b")
        self.assertIs(premier, second)

    def test_les_arguments_suivants_sont_ignores(self):
        Corpus("premier")
        self.assertEqual(Corpus("second").nom, "premier")

    def test_l_etat_est_partage(self):
        Corpus("a").add_document(Document("T", "alice", None, "u", "x"))
        self.assertEqual(Corpus("b").ndoc, 1)

    def test_init_n_est_pas_rappele(self):
        corpus = Corpus("a")
        corpus.add_document(Document("T", "alice", None, "u", "x"))
        Corpus("a")  # ne doit pas remettre le corpus à zéro
        self.assertEqual(corpus.ndoc, 1)

    def test_reinitialiser_donne_un_nouveau_corpus_vide(self):
        ancien = Corpus("a")
        ancien.add_document(Document("T", "alice", None, "u", "x"))
        Corpus.reinitialiser()
        nouveau = Corpus("b")
        self.assertIsNot(nouveau, ancien)
        self.assertEqual(nouveau.ndoc, 0)

    def test_chaque_classe_a_sa_propre_instance(self):
        class Autre(metaclass=Singleton):
            pass
        self.assertIsNot(Autre(), Corpus("a"))
        Autre.reinitialiser()


class TestFactory(unittest.TestCase):
    CHAMPS = ("Titre", "alice", "2021-05-01T10:00:00Z", "http://x", "texte")

    def test_cree_un_document_hacker_news(self):
        doc = DocumentFactory.creer("Hacker News", *self.CHAMPS, nb_commentaires=5)
        self.assertIsInstance(doc, HackerNewsDocument)
        self.assertEqual(doc.get_nb_commentaires(), 5)

    def test_cree_un_document_arxiv(self):
        doc = DocumentFactory.creer("Arxiv", *self.CHAMPS, co_auteurs=["Bob B"])
        self.assertIsInstance(doc, ArxivDocument)
        self.assertEqual(doc.get_co_auteurs(), ["Bob B"])

    def test_cree_un_document_simple(self):
        doc = DocumentFactory.creer("Document", *self.CHAMPS)
        self.assertIs(type(doc), Document)

    def test_champs_specifiques_facultatifs(self):
        self.assertEqual(DocumentFactory.creer("Hacker News", *self.CHAMPS).get_nb_commentaires(), 0)
        self.assertEqual(DocumentFactory.creer("Arxiv", *self.CHAMPS).get_co_auteurs(), [])

    def test_type_inconnu(self):
        with self.assertRaises(ValueError) as contexte:
            DocumentFactory.creer("Reddit", *self.CHAMPS)
        self.assertIn("Reddit", str(contexte.exception))

    def test_champ_incompatible_avec_le_type(self):
        with self.assertRaises(ValueError):
            DocumentFactory.creer("Arxiv", *self.CHAMPS, nb_commentaires=3)

    def test_aller_retour_to_dict_puis_creer(self):
        # La fabrique sait reconstruire un document à partir de ce que to_dict() produit
        for original in (
            HackerNewsDocument(*self.CHAMPS, nb_commentaires=9),
            ArxivDocument(*self.CHAMPS, co_auteurs=["Bob B", "Carol C"]),
            Document(*self.CHAMPS),
        ):
            copie = DocumentFactory.creer(**original.to_dict())
            self.assertIs(type(copie), type(original))
            self.assertEqual(str(copie), str(original))


class TestSauvegardeDesTypes(TestAvecCorpusVierge):
    def remplir(self):
        corpus = Corpus("test")
        corpus.add_document(HackerNewsDocument("Post", "alice", "2021-05-01T10:00:00Z",
                                               "http://hn", "texte hn", 12))
        corpus.add_document(ArxivDocument("Article, avec virgule et \"guillemets\"", "Bob B",
                                          "2022-01-01T10:00:00Z", "http://arxiv", "texte\narxiv",
                                          ["Carol C", "Dan D, Jr", "Éve"]))
        corpus.add_document(HackerNewsDocument("Post sans commentaire", "alice", None,
                                               "http://hn2", "texte", 0))
        corpus.add_document(Document("Document simple", "zoe", None, "http://d", "texte"))
        return corpus

    def test_aller_retour_conserve_classes_et_champs_specifiques(self):
        corpus = self.remplir()
        avant = [(type(d), str(d), d.getType(), d.date) for d in corpus.id2doc.values()]
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "c.csv"
            corpus.save(chemin)
            recharge = Corpus.load(chemin)
        apres = [(type(d), str(d), d.getType(), d.date) for d in recharge.id2doc.values()]
        self.assertEqual(apres, avant)

    def test_aller_retour_conserve_les_listes_et_les_textes(self):
        corpus = self.remplir()
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "c.csv"
            corpus.save(chemin)
            recharge = Corpus.load(chemin)
        self.assertEqual(recharge.id2doc[1].get_co_auteurs(), ["Carol C", "Dan D, Jr", "Éve"])
        self.assertEqual(recharge.id2doc[1].texte, "texte\narxiv")
        self.assertEqual(recharge.id2doc[0].get_nb_commentaires(), 12)
        self.assertEqual(recharge.id2doc[2].get_nb_commentaires(), 0)

    def test_le_csv_contient_les_colonnes_de_type(self):
        corpus = self.remplir()
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "c.csv"
            corpus.save(chemin)
            entete = chemin.read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(entete.split("\t"), ["id", "titre", "auteur", "date", "url", "texte",
                                              "type_doc", "nb_commentaires", "co_auteurs"])

    def test_ancien_csv_sans_type_recharge_en_documents_simples(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "ancien.csv"
            chemin.write_text("id\ttitre\tauteur\tdate\turl\ttexte\n"
                              "0\tVieux\talice\t2020-01-01T00:00:00\thttp://x\tbonjour\n",
                              encoding="utf-8")
            recharge = Corpus.load(chemin)
        self.assertIs(type(recharge.id2doc[0]), Document)
        self.assertEqual(recharge.id2doc[0].getType(), "Document")

    def test_load_remplace_le_corpus_unique(self):
        corpus = self.remplir()
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "c.csv"
            corpus.save(chemin)
            recharge = Corpus.load(chemin)
            Corpus.load(chemin)  # recharger deux fois ne doit pas doubler les documents
        self.assertEqual(recharge.ndoc, 4)
        self.assertEqual(Corpus("autre").ndoc, 4)

    def test_fichier_invalide_ne_detruit_pas_le_corpus_existant(self):
        corpus = Corpus("existant")
        corpus.add_document(Document("T", "alice", None, "u", "x"))
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "td3.csv"
            chemin.write_text("id\ttexts\torg\n0\tbonjour\thackernews\n", encoding="utf-8")
            with self.assertRaises(KeyError):
                Corpus.load(chemin)
        self.assertIs(Corpus("autre"), corpus)
        self.assertEqual(corpus.ndoc, 1)

    def test_type_inconnu_dans_le_csv(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "c.csv"
            chemin.write_text("id\ttitre\tauteur\tdate\turl\ttexte\ttype_doc\n"
                              "0\tT\ta\t\tu\tx\tReddit\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                Corpus.load(chemin)


if __name__ == "__main__":
    unittest.main()
