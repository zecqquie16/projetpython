import urllib.request
import urllib.parse
import json
import html
import xmltodict
import pandas as pd

docs =[]
thematique = "coronavirus"
org = []
len_donnees = 50

def init(docs, thematique, org):
    # 1.1
    url_hn = "https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode({"query": thematique, "tags": "story", "hitsPerPage": len_donnees})
    print("URL HN:", url_hn)

    with urllib.request.urlopen(url_hn) as resp_hn:
        res_hn = json.load(resp_hn)

    print("HN Response Keys:", res_hn.keys())  # Affiche la liste des champs disponibles

    # Le champs qui contient du texte est story_text. 
    # Il est absent des documents qui ne pointent que vers un lien extérieur : 
    # dans ce cas on choisi le champ "title".

    for hit in res_hn["hits"]: # on teste si le champs story_text est présent, sinon on prend le champs titre
        texte = hit.get("story_text")
        if not texte:
            texte = hit.get("title", "")
        texte = html.unescape(texte).replace("<p>", " ").strip() # retire la balise html du texte
        docs.append(texte)
        org.append("hackernews")
    print("Taille du corpus :", len(docs))
    print("Exemple de document pour HN :", docs[0])

    # 1.2
    url_arxiv = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": "all:" + thematique, "start": 0,"max_results": len_donnees})
    print("URL Arxiv:", url_arxiv)

    with urllib.request.urlopen(url_arxiv) as resp_arxiv:
        res_arxiv = xmltodict.parse(resp_arxiv.read())

    print("Arxiv Response Keys:", res_arxiv.keys())  # Affiche la racine du doc XML
    print("Arxiv Feed Keys:", res_arxiv["feed"].keys())  # Affiche les champs disponibles pour un article

    # Il faut traiter le cas où il n'y a qu'un seul résultat, 
    # xmltodict renvoie un simple dictionnaire et non une liste ; 
    # s'il n'y en a aucun, la clef entry est absente.
    entrys = res_arxiv["feed"].get("entry", [])
    if isinstance(entrys, dict):
        entrys = [entrys]
    print("Nombre de documents récupérés pour Arxiv :", len(entrys))
    print("Exemple de document pour Arxiv :", entrys[0].keys())

    for entry in entrys:
        texte = entry["summary"].replace("\n", " ").strip()
        docs.append(texte)
        org.append("arxiv")
    print("Taille du corpus :", len(docs))
    print("Exemple de document pour Arxiv :", docs[-1])

    # 2.1
    df = pd.DataFrame({"id": range(len(docs)),
                   "texts": docs,
                   "org": org})
    
    # 2.2
    df.to_csv("corpus.csv", sep="\t", index=False)

    return df
# 2.3
df = pd.read_csv("corpus.csv", sep="\t")


# 3.1
print("Taille du corpus :", len(df))


# 3.2
for text in df["texts"]:
    words = text.split(" ")
    sentences = text.split(".")
    print(len(words), "mots et", len(sentences), "phrases")


# 3.3
print("Avant la suppression :", len(df))
df = df[df["texts"].str.len() >= 20]
print("Après la suppression :", len(df))


# 3.4
chain = " ".join(df["texts"])
print(len(chain), "caractères au total")