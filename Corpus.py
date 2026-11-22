import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from Author import Author
from DocumentFactory import DocumentFactory
from Singleton import Singleton

# Colonnes du CSV. Celles de la fin sont propres à un type de document :
# nb_commentaires (Hacker News) et co_auteurs (Arxiv), vides pour les autres.
COLONNES = ["id", "titre", "auteur", "date", "url", "texte",
            "type_doc", "nb_commentaires", "co_auteurs"]


class Corpus(metaclass=Singleton):
    """Collection de documents et d'auteurs.

    Singleton (TD5 4.1) : on ne traite qu'un seul corpus, donc Corpus("a") et
    Corpus("b") renvoient le même objet.
    """

    def __init__(self, nom):
        self.nom = nom
        self.authors = {}  # nom de l'auteur -> Author
        self.id2doc = {}   # id du document -> Document
        self.ndoc = 0
        self.naut = 0

    def add_document(self, document):
        """Ajoute un document (de n'importe quelle classe fille) et met à jour l'auteur."""
        doc_id = self.ndoc
        self.id2doc[doc_id] = document
        self.ndoc += 1

        # si nouvel auteur On le crée seulement s'il n'est pas déjà connu
        if document.auteur not in self.authors:
            self.authors[document.auteur] = Author(document.auteur)
            self.naut += 1
        self.authors[document.auteur].add(doc_id, document)

    def stats_auteur(self, nom):
        """Affiche le nombre de documents et la taille moyenne pour un auteur."""
        if nom not in self.authors:
            print(f"Auteur inconnu : {nom}")
            return
        auteur = self.authors[nom]
        print(f"{auteur.name} : {auteur.ndoc} document(s), "
              f"taille moyenne {auteur.taille_moyenne():.0f} caractères")

    def afficher_par_date(self, n=5):
        """Affiche les n documents les plus récents."""
        docs = sorted(self.id2doc.values(),
                      key=lambda d: d.date or datetime.min,
                      reverse=True)
        for doc in docs[:n]:
            print(f"{doc.date} | {doc.titre}")

    def afficher_par_titre(self, n=5):
        """Affiche les n premiers documents par ordre alphabétique du titre."""
        docs = sorted(self.id2doc.values(), key=lambda d: d.titre.lower())
        for doc in docs[:n]:
            print(f"{doc.titre} | {doc.auteur}")

    def sources(self):
        """Retourne la liste triée des sources présentes dans le corpus (TD5 3.2)."""
        return sorted({doc.getType() for doc in self.id2doc.values()})

    def afficher_liste(self, n=None, type_doc=None):
        """Affiche les documents avec leur source (TD5 3.2).

        n : nombre maximum de documents affichés (None = tous)
        type_doc : ne garder que cette source ("Hacker News" ou "Arxiv")

        Polymorphisme : on appelle getType() et str(doc) sans savoir de quelle
        classe fille il s'agit, chaque classe répond à sa façon.
        """
        docs = [(doc_id, doc) for doc_id, doc in self.id2doc.items()
                if type_doc is None or doc.getType() == type_doc]
        for doc_id, doc in docs[:n]:
            print(f"{doc_id:>3} [{doc.getType()}] {doc}")

    def save(self, chemin):
        """Enregistre le corpus dans un CSV (séparateur tabulation) via un DataFrame."""
        lignes = []
        for doc_id, doc in self.id2doc.items():
            ligne = {colonne: "" for colonne in COLONNES}  # cellules vides par défaut
            ligne["id"] = doc_id
            ligne.update(doc.to_dict())  # polymorphisme : chaque classe donne ses champs
            # Une liste (co_auteurs) tient dans une seule cellule : on l'écrit en JSON
            for cle, valeur in list(ligne.items()):
                if isinstance(valeur, list):
                    ligne[cle] = json.dumps(valeur, ensure_ascii=False)
            lignes.append(ligne)
        df = pd.DataFrame(lignes, columns=COLONNES)
        chemin = Path(chemin)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(chemin, sep="\t", index=False)

    @classmethod
    def load(cls, chemin, nom=None):
        """Recharge un corpus depuis un CSV créé par save().

        Un CSV ancien (sans colonne type_doc) est rechargé avec des Document simples.
        """
        chemin = Path(chemin)
        # dtype=str : tout est lu comme du texte (pas de "12.0" ni de NaN), on convertit nous-mêmes
        df = pd.read_csv(chemin, sep="\t", dtype=str, keep_default_na=False)

        # 1) On fabrique d'abord tous les documents : si le fichier est invalide,
        #    l'erreur est levée ici, avant de toucher au corpus unique.
        documents = []
        for _, ligne in df.iterrows():
            specifique = {}
            if ligne.get("nb_commentaires", ""):
                specifique["nb_commentaires"] = int(ligne["nb_commentaires"])
            if ligne.get("co_auteurs", ""):
                specifique["co_auteurs"] = json.loads(ligne["co_auteurs"])
            # La fabrique choisit la bonne classe selon la colonne type_doc
            documents.append(DocumentFactory.creer(
                ligne.get("type_doc") or "Document",
                ligne["titre"], ligne["auteur"], ligne["date"],
                ligne["url"], ligne["texte"],
                **specifique,
            ))

        # 2) Singleton : charger = remplacer l'unique corpus par celui du fichier
        cls.reinitialiser()
        corpus = cls(nom if nom else chemin.stem)
        for document in documents:
            corpus.add_document(document)
        return corpus

    def __repr__(self):
        return f"Corpus '{self.nom}' : {self.ndoc} documents, {self.naut} auteurs"