# Guide d'implémentation : `lib-embedding`

## Pourquoi un client d'embedding ?

Dans un système RAG, on doit transformer du texte en **vecteurs numériques** pour pouvoir chercher par similarité. Le modèle `all-MiniLM-L6-v2` prend une phrase en entrée et produit un vecteur de **384 floats** qui représente son sens.

```
"Bulbizarre est un Pokémon de type Plante"
        ↓ encode()
[0.032, -0.118, 0.045, ..., 0.091]   ← 384 nombres
```

Deux textes qui parlent de la même chose auront des vecteurs proches (similarité cosinus élevée). C'est ce qui permet la **recherche sémantique** : on vectorise la requête utilisateur, puis on cherche les chunks les plus proches dans pgvector.

### Ce qu'on encapsule

La bibliothèque `sentence-transformers` fait le gros du travail. Notre classe `EmbeddingClient` l'encapsule pour :
- Charger le modèle une seule fois (dans `__init__`)
- Exposer une méthode `encode()` qui prend des strings et retourne des `list[float]`
- Exposer la dimension du modèle via une property

---

## Ce qui est fourni

Le `__init__` et la property `dimension` sont déjà implémentés :

```python
class EmbeddingClient:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model = SentenceTransformer(model_name)

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()
```

## Ce qui est à implémenter

La méthode `encode` :

```python
def encode(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
```

## Règles déduites des tests

| Règle | Test correspondant |
|-------|-------------------|
| Liste vide en entrée → `[]` en sortie | `test_encode_empty` |
| Un seul texte → une liste contenant un vecteur de 384 floats | `test_encode_single` |
| Chaque élément du vecteur est un `float` Python (pas un `numpy.float32`) | `test_encode_single` |
| Plusieurs textes → autant de vecteurs, chacun de dimension 384 | `test_encode_batch` |
| Le paramètre `batch_size` est passé au modèle (traitement par lots) | `test_encode_batch` |

## Indice

`self._model.encode(texts, batch_size=batch_size)` retourne un **numpy array** de shape `(n, 384)`. Les tests attendent des `list[float]` Python, pas des `numpy.float32`.

## Exemple pas à pas

```
texts = ["Salamèche crache du feu", "Carapuce lance un jet d'eau"]
batch_size = 32

→ Étape 1 : texts est non vide (2 éléments)

→ Étape 2 : self._model.encode(texts, batch_size=32)
  Retourne un numpy.ndarray de shape (2, 384) :
  array([[ 0.032, -0.118,  0.045, ...,  0.091],    ← "Salamèche..."
         [-0.057,  0.203,  0.011, ..., -0.044]])    ← "Carapuce..."

→ Étape 3 : convertir chaque vecteur numpy en list[float] Python

Résultat : [
    [0.032, -0.118, 0.045, ..., 0.091],     ← list[float], len=384
    [-0.057, 0.203, 0.011, ..., -0.044]      ← list[float], len=384
]
```

## Conseil

C'est ~4 lignes de code. L'essentiel est de ne pas oublier la conversion numpy → list Python.
