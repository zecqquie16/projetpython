from Corpus import Corpus
from Document import Document

CHEMIN_CSV = "data/corpus.csv"


def main():
    # Pour l'instant : faux documents, en attendant acquisition.py (TD3)
    corpus = Corpus("demo")
    corpus.add_document(Document("Climate and AI", "Alice", "2024-03-01T10:00:00Z", "http://a", "Un texte sur le climat."))
    corpus.add_document(Document("Arctic ice", "Bob", "2024-05-12T08:30:00Z", "http://b", "Un autre texte, un peu plus long."))
    corpus.add_document(Document("Carbon markets", "Alice", "2023-11-20T16:45:00Z", "http://c", "Court."))

    print(corpus)
    print("\n--- Par date ---")
    corpus.afficher_par_date(2)
    print("\n--- Par titre ---")
    corpus.afficher_par_titre(3)
    print("\n--- Stats ---")
    corpus.stats_auteur("Alice")

    corpus.save(CHEMIN_CSV)
    recharge = Corpus.load(CHEMIN_CSV)
    print("\nRechargé :", recharge)


if __name__ == "__main__":
    main()