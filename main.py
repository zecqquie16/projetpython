"""
    python main.py              # load data/corpus.csv s'il existe, sinon interroge les APIs
    python main.py --refresh    # force un nouveau téléchargement depuis les APIs
    qui couvre l'indépendance d'Internet demandée au td3
"""

import sys
from pathlib import Path
from xml.parsers.expat import ExpatError

from Acquisition import fetch_arxiv, fetch_hackernews
from Corpus import Corpus
from Document import Document

THEMATIQUE = "coronavirus"      
NB_DOCS_PAR_SOURCE = 50
MIN_CARACTERES = 20              # TD3 3.3 : on écarte les documents trop petits
CHEMIN_CSV = Path(__file__).resolve().parent / "data" / "corpus.csv"

# Erreurs attendues lors d'un appel d'API : réseau, JSON invalide, XML invalide
ERREURS_ACQUISITION = (OSError, ValueError, ExpatError)


def construire_corpus(thematique, nb_docs):
    """Interroge Hacker News et Arxiv puis remplit un Corpus.

    Si une source est indisponible, on le signale et on continue avec l'autre
    au lieu de faire planter le programme.
    """
    corpus = Corpus(thematique)
    sources = [("Hacker News", fetch_hackernews), ("Arxiv", fetch_arxiv)]

    for nom_source, fetch in sources:
        try:
            documents = fetch(thematique, nb_docs)
        except ERREURS_ACQUISITION as erreur:
            print(f"[!] {nom_source} indisponible ({erreur}), source ignorée.")
            continue

        ajoutes = 0
        for doc in documents:
            if len(doc["texte"]) < MIN_CARACTERES:
                continue
            corpus.add_document(
                Document(doc["titre"], doc["auteur"], doc["date"], doc["url"], doc["texte"])
            )
            ajoutes += 1
        print(f"{nom_source} : {ajoutes} document(s) ajouté(s).")

    return corpus


def charger_ou_construire(rafraichir=False):
    """Recharge le corpus depuis le CSV s'il existe, sinon l'acquiert via les APIs."""
    if CHEMIN_CSV.exists() and not rafraichir:
        try:
            corpus = Corpus.load(CHEMIN_CSV, nom=THEMATIQUE)
            print(f"Corpus rechargé depuis {CHEMIN_CSV.name}.")
            return corpus
        except (OSError, ValueError, KeyError) as erreur:
            # Fichier illisible ou colonnes inattendues : on repart des APIs
            print(f"[!] Impossible de relire {CHEMIN_CSV.name} ({erreur}), nouvelle acquisition.")

    corpus = construire_corpus(THEMATIQUE, NB_DOCS_PAR_SOURCE)
    if corpus.ndoc > 0:
        corpus.save(CHEMIN_CSV)
        print(f"Corpus sauvegardé dans {CHEMIN_CSV.name}.")
    else:
        print("[!] Aucun document récupéré : rien n'a été sauvegardé.")
    return corpus


def afficher_apercu(corpus):
    """Affiche un aperçu du corpus : taille, derniers documents, ordre alphabétique."""
    print("\n", corpus, sep="")
    print("\n--- 5 documents les plus récents ---")
    corpus.afficher_par_date(5)
    print("\n--- 5 premiers documents par titre ---")
    corpus.afficher_par_titre(5)


def menu_stats_auteur(corpus):
    """Demande un nom d'auteur à l'utilisateur et affiche ses statistiques (TD4 2.4)."""
    exemples = ", ".join(list(corpus.authors)[:5])
    print(f"\n--- Statistiques par auteur --- (exemples : {exemples})")
    while True:
        try:
            nom = input("Nom d'un auteur (Entrée pour quitter) : ").strip()
        except EOFError:  # pas de clavier (exécution automatique) : on s'arrête
            break
        if not nom:
            break
        corpus.stats_auteur(nom)


def main():
    corpus = charger_ou_construire(rafraichir="--refresh" in sys.argv)
    if corpus.ndoc == 0:
        return
    afficher_apercu(corpus)
    menu_stats_auteur(corpus)


if __name__ == "__main__":
    main()