"""Acquisition des documents depuis Hacker News (JSON) et Arxiv (XML).

La logique d'appel des APIs et de nettoyage reprend celle du script td3.py de
Chahid (TD3). On y ajoute l'extraction de métadonnées nécessaires (titre,
auteur, date, url) dont les classes Document / Author / Corpus (TD4) ont besoin.

Chaque fonction fetch_* renvoie une liste de dictionnaires avec les clés :
titre, auteur, date, url, texte.

Le découpage "appel réseau" / "analyse de la réponse" permet de tester
l'analyse (_parser_hn, _parser_arxiv) sans accès à Internet.
"""

import html
import json
import urllib.parse
import urllib.request

import xmltodict

URL_HN = "https://hn.algolia.com/api/v1/search?"
URL_ARXIV = "http://export.arxiv.org/api/query?"
URL_ITEM_HN = "https://news.ycombinator.com/item?id="
AUTEUR_INCONNU = "inconnu"
TIMEOUT_SECONDES = 30


def _nettoyer_hn(texte):
    """Nettoie un texte Hacker News : balises <p> -> espace, entités HTML décodées."""
    return html.unescape(texte).replace("<p>", " ").strip()


def _nettoyer_arxiv(texte):
    """Nettoie un texte Arxiv : sauts de ligne et espaces multiples -> un seul espace."""
    return " ".join(texte.split())


def _parser_hn(resultat):
    
    documents = []
    for hit in resultat.get("hits", []):
        titre = hit.get("title") or ""
        # story_text est absent des posts qui ne contiennent qu'un lien : repli sur le titre
        texte = _nettoyer_hn(hit.get("story_text") or titre)
        # Les posts texte n'ont pas d'url externe : on pointe vers la page Hacker News
        url = hit.get("url") or URL_ITEM_HN + str(hit.get("objectID", ""))
        documents.append({
            "titre": titre,
            "auteur": hit.get("author") or AUTEUR_INCONNU,
            "date": hit.get("created_at"),
            "url": url,
            "texte": texte,
        })
    return documents


def _parser_arxiv(contenu_xml):
    flux = xmltodict.parse(contenu_xml)
    entrees = (flux.get("feed") or {}).get("entry", [])
    # xmltodict renvoie un simple dict (et non une liste) s'il n'y a qu'un résultat,
    # et la clé "entry" est absente s'il n'y en a aucun.
    if isinstance(entrees, dict):
        entrees = [entrees]

    documents = []
    for entree in entrees:
        auteurs = entree.get("author") or []
        # Même piège que pour entry : un seul auteur donne un dict, plusieurs une liste
        if isinstance(auteurs, dict):
            auteurs = [auteurs]
        # Un document n'a qu'un auteur dans notre modèle : on garde le premier
        premier_auteur = auteurs[0].get("name") if auteurs else None
        documents.append({
            "titre": _nettoyer_arxiv(entree.get("title") or ""),
            "auteur": premier_auteur or AUTEUR_INCONNU,
            "date": entree.get("published"),
            "url": entree.get("id") or "",
            "texte": _nettoyer_arxiv(entree.get("summary") or ""),
        })
    return documents


def fetch_hackernews(keyword, n=50):
    
    parametres = urllib.parse.urlencode(
        {"query": keyword, "tags": "story", "hitsPerPage": n}
    )
    with urllib.request.urlopen(URL_HN + parametres, timeout=TIMEOUT_SECONDES) as reponse:
        resultat = json.load(reponse)
    return _parser_hn(resultat)


def fetch_arxiv(keyword, n=50):
    
    
    parametres = urllib.parse.urlencode(
        {"search_query": "all:" + keyword, "start": 0, "max_results": n}
    )
    with urllib.request.urlopen(URL_ARXIV + parametres, timeout=TIMEOUT_SECONDES) as reponse:
        contenu = reponse.read()
    return _parser_arxiv(contenu)