from datetime import datetime


def convertir_date(date):
    """Convertit une date (str ISO ou datetime) en datetime sans fuseau.

    Retourne None si la date est absente ou illisible.
    Hacker News et Arxiv donnent des dates ISO du type 2024-03-01T10:00:00Z.
    """
    if isinstance(date, datetime):
        return date.replace(tzinfo=None)
    try:
        # En Python 3.10, fromisoformat ne comprend pas le "Z" final
        return datetime.fromisoformat(str(date).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


class Document:
    """Un document du corpus (post Hacker News ou article Arxiv)."""

    def __init__(self, titre, auteur, date, url, texte):
        self.titre = titre
        self.auteur = auteur
        self.date = convertir_date(date)  # datetime ou None
        self.url = url
        self.texte = texte

    def afficher(self):
        """Affiche toutes les informations du document."""
        print(f"Titre  : {self.titre}")
        print(f"Auteur : {self.auteur}")
        print(f"Date   : {self.date}")
        print(f"URL    : {self.url}")
        print(f"Texte  : {self.texte[:200]}...")

    def __str__(self):
        """Version courte : le titre seulement (utilisé par print(doc))."""
        return self.titre


class HackerNewsDocument(Document):
    """Document provenant de Hacker News."""

    def __init__(self, titre, auteur, date, url, texte, nb_commentaires):
        super().__init__(titre, auteur, date, url, texte)
        self.source = "Hacker News"
        self.nb_commentaires = nb_commentaires

    def get_nb_commentaires(self):
        """Retourne le nombre de commentaires du post Hacker News."""
        return self.nb_commentaires

    def set_nb_commentaires(self, nb):
        """Met à jour le nombre de commentaires du post Hacker News."""
        self.nb_commentaires = nb

    def __str__(self):
        """Version complète : Utilise le titre et le nombre de commentaires (utilisé par print(doc))."""
        return f"{self.titre} ({self.nb_commentaires} commentaires)"

class ArxivDocument(Document):
    """Document provenant d'Arxiv."""

    def __init__(self, titre, auteur, date, url, texte, co_auteurs):
        super().__init__(titre, auteur, date, url, texte)
        self.co_auteurs = list(co_auteurs)  # liste des co-auteurs

    def get_co_auteurs(self):
        """Retourne la liste des co-auteurs de l'article Arxiv."""
        return self.co_auteurs

    def set_co_auteurs(self, co_auteurs):
        """Met à jour la liste des co-auteurs de l'article Arxiv."""
        self.co_auteurs = list(co_auteurs)

    def add_co_auteur(self, co_auteur):
        """Ajoute un co-auteur à la liste des co-auteurs de l'article Arxiv, si et seulement s'il n'est pas déjà présent."""
        if co_auteur not in self.co_auteurs:
            self.co_auteurs.append(co_auteur)

    def __str__(self):
        """Version complète : Utilise le titre et la liste des co-auteurs (utilisé par print(doc))."""
        co_auteurs_str = ", ".join(self.co_auteurs)
        return f"{self.titre} (Co-auteurs : {co_auteurs_str})"
