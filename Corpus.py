from datetime import datetime
from pathlib import Path

import pandas as pd

from Author import Author
from Document import Document


class Corpus:
    """Collection de documents et d'auteurs."""

    def __init__(self, nom):
        self.nom = nom
        self.authors = {}  # nom de l'auteur -> Author
        self.id2doc = {}   # id du document -> Document
        self.ndoc = 0
        self.naut = 0

    def add_document(self, document):
        """Ajoute un document et met à jour l'auteur correspondant."""
        doc_id = self.ndoc
        self.id2doc[doc_id] = document
        self.ndoc += 1

        # Nouvel auteur ? On le crée seulement s'il n'est pas déjà connu
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

    def save(self, chemin):
        """Enregistre le corpus dans un CSV (séparateur tabulation) via un DataFrame."""
        lignes = []
        for doc_id, doc in self.id2doc.items():
            lignes.append({
                "id": doc_id,
                "titre": doc.titre,
                "auteur": doc.auteur,
                "date": doc.date.isoformat() if doc.date else "",
                "url": doc.url,
                "texte": doc.texte,
            })
        df = pd.DataFrame(lignes, columns=["id", "titre", "auteur", "date", "url", "texte"])
        chemin = Path(chemin)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(chemin, sep="\t", index=False)

    @classmethod
    def load(cls, chemin, nom=None):
        """Recharge un corpus depuis un CSV créé par save()."""
        chemin = Path(chemin)
        df = pd.read_csv(chemin, sep="\t").fillna("")
        corpus = cls(nom if nom else chemin.stem)
        for _, ligne in df.iterrows():
            corpus.add_document(Document(
                ligne["titre"], ligne["auteur"], ligne["date"],
                ligne["url"], ligne["texte"],
            ))
        return corpus

    def __repr__(self):
        return f"Corpus '{self.nom}' : {self.ndoc} documents, {self.naut} auteurs"