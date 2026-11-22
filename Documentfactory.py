

from Document import ArxivDocument, Document, HackerNewsDocument


class DocumentFactory:
    """Crée le bon type de document à partir du nom de sa source.


    """

    TYPES = {
        "Document": Document,
        "Hacker News": HackerNewsDocument,
        "Arxiv": ArxivDocument,
    }

    @classmethod
    def creer(cls, type_doc, titre, auteur, date, url, texte, **specifique):
        """Retourne un document du type demandé.

        type_doc : "Hacker News", "Arxiv" ou "Document"
        specifique : champs propres à la classe (nb_commentaires, co_auteurs...)
        Lève ValueError si le type est inconnu ou si les champs ne lui conviennent pas.
        """
        classe = cls.TYPES.get(type_doc)
        if classe is None:
            connus = ", ".join(cls.TYPES)
            raise ValueError(f"Type de document inconnu : {type_doc!r} (types connus : {connus})")
        try:
            return classe(titre, auteur, date, url, texte, **specifique)
        except TypeError as erreur:
            raise ValueError(f"Champs incompatibles avec le type {type_doc!r} : {erreur}") from erreur