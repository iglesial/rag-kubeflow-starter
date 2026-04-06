# Guide d'implémentation : `routes/search.py`

## Pourquoi cette route ?

C'est le coeur du système RAG. Quand un utilisateur pose une question, cette route :

1. Transforme la question en vecteur (384 floats)
2. Cherche les chunks les plus similaires dans pgvector
3. Retourne les résultats classés par pertinence

```
POST /search  {"query": "quel Pokémon crache du feu ?"}
    ↓
  encode("quel Pokémon crache du feu ?") → [0.03, -0.11, ..., 0.09]
    ↓
  SELECT ... FROM document_chunks WHERE similarity >= 0.5 ORDER BY similarity DESC
    ↓
  {"results": [{"document_name": "004-salameche.md", "similarity_score": 0.82, ...}]}
```

---

## Ce qui est fourni

La signature de la route avec l'injection de dépendances :

```python
@router.post("/search")
async def search(
    body: SearchRequest,
    session: AsyncSession = Depends(get_db_session),
    client: EmbeddingClient = Depends(get_embedding_client),
) -> SearchResponse:
```

- `body` contient : `query` (str), `top_k` (int), `similarity_threshold` (float)
- `session` est une session async SQLAlchemy (prête à l'emploi)
- `client` est le client d'embedding (méthode `encode()`)

## Ce qui est à implémenter

Le corps de la fonction : les 3 étapes.

## Les schémas à votre disposition

Consultez `lib-schemas` — les schémas vous disent exactement quoi retourner :

| Schéma | Champs |
|--------|--------|
| `SearchRequest` | `query`, `top_k`, `similarity_threshold` |
| `SearchResult` | `chunk_id`, `document_name`, `content`, `similarity_score`, `metadata` |
| `SearchResponse` | `query`, `results`, `total_results`, `embedding_time_ms`, `search_time_ms` |

## Règles déduites des tests

| Règle | Test correspondant |
|-------|-------------------|
| La requête est encodée via `client.encode([query])` | `test_search_returns_results` |
| Les résultats sont classés par score de similarité décroissant | `test_search_returns_results` |
| La réponse contient `embedding_time_ms` et `search_time_ms` | `test_search_returns_results` |
| Base vide → `results: []`, `total_results: 0` | `test_search_empty_db` |
| Query vide → 422 (géré par le schéma Pydantic) | `test_search_empty_query_rejected` |
| `top_k=1` → au plus 1 résultat | `test_search_top_k_one` |
| `top_k=0` → 422 (géré par le schéma Pydantic) | `test_search_invalid_top_k` |

---

## Indices progressifs

### Indice 1 — Les 3 étapes

Votre route fait exactement 3 choses, dans l'ordre :

1. **Encoder** la query → un vecteur de 384 floats
2. **Chercher** dans pgvector → requête SQL avec similarité cosinus
3. **Construire** la réponse → `SearchResponse` avec résultats + chronométrage

Pour le chronométrage, `time.perf_counter()` mesure le temps écoulé en secondes (à convertir en millisecondes).

### Indice 2 — La requête pgvector

En SQL pur, une recherche par similarité cosinus ressemble à :

```sql
SELECT *, 1 - (embedding <=> '[0.03, -0.11, ...]') AS similarity
FROM document_chunks
WHERE similarity >= 0.5
ORDER BY similarity DESC
LIMIT 5;
```

L'opérateur `<=>` calcule la **distance** cosinus (pas la similarité). Le piège :

```
distance = 0   → textes identiques
distance = 1   → textes orthogonaux

similarité = 1 - distance
```

En SQLAlchemy, le modèle `DocumentChunk` expose une méthode sur la colonne `embedding` :

```python
DocumentChunk.embedding.cosine_distance(query_vector)
```

Il faut donc calculer `1 - cosine_distance(...)` et lui donner un `.label("similarity")` pour l'utiliser dans le `WHERE` et le `ORDER BY`.

### Indice 3 — La structure des lignes retournées

`await session.execute(stmt)` retourne un objet Result. Appelez `.all()` pour obtenir la liste des lignes.

Chaque ligne a **deux attributs** (parce que le `select()` contient le modèle + la colonne calculée) :

```python
row.DocumentChunk    # l'objet ORM → .id, .document_name, .content, .metadata_
row.similarity       # le float calculé
```

Il reste à construire un `SearchResult` pour chaque ligne et à les emballer dans un `SearchResponse`.
