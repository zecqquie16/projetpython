class Author:
    """Un auteur et l'ensemble de ses documents."""

    def __init__(self, name):
        self.name = name
        self.ndoc = 0
        self.production = {}  # id du document -> Document

    def add(self, doc_id, document):
        """Ajoute un document à la production de l'auteur."""
        self.production[doc_id] = document
        self.ndoc += 1

    def taille_moyenne(self):
        """Taille moyenne (en caractères) des textes de l'auteur."""
        if self.ndoc == 0:
            return 0
        total = sum(len(doc.texte) for doc in self.production.values())
        return total / self.ndoc

    def __str__(self):
        return f"{self.name} ({self.ndoc} document(s))"