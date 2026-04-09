# Guide d'implémentation : `rag-generator`

## Pourquoi ce package ?

Jusqu'ici, le système est en **retrieval-only** : on pose une question, on récupère les chunks les plus pertinents, mais on ne génère pas de réponse en langage naturel. C'est le "R" de RAG sans le "G".

Le `rag-generator` ferme la boucle :

```
POST /generate  {"question": "Quel type est Pikachu ?"}
    ↓
  1. Appel au retriever → chunks pertinents
    ↓
  2. Construction du prompt (question + contexte)
    ↓
  3. Appel à Ollama (LLM local) → réponse générée
    ↓
  {"answer": "Pikachu est de type Électrik.", "sources": [...]}
```

```
┌──────────┐      POST /search       ┌──────────────┐
│          │ ──────────────────────►  │ rag-retriever│ ──► pgvector
│   rag-   │ ◄──────────────────────  │   :8000      │
│generator │      SearchResponse      └──────────────┘
│  :8001   │
│          │    POST /api/generate    ┌──────────────┐
│          │ ──────────────────────►  │   Ollama     │
│          │ ◄──────────────────────  │   :11434     │
└──────────┘      réponse LLM        └──────────────┘
```

Le generator est une **couche d'orchestration** légère : il ne touche pas à la base de données, ne fait pas d'embedding — il compose deux services via HTTP.

---

## Prérequis

- PostgreSQL + pgvector fonctionnel (`docker compose ps`)
- Données chargées et indexées (`just pipeline`)
- Le retriever fonctionne (`just serve` dans un terminal)

## Étape 0 : Ajouter Ollama au `docker-compose.yml`

### Qu'est-ce qu'Ollama ?

Ollama est un serveur local qui fait tourner des LLM open-source (Phi, Llama, Mistral…). Il expose une API REST sur le port `11434` — on lui envoie un prompt en HTTP, il retourne la réponse du modèle. C'est l'équivalent local de l'API d'OpenAI, mais gratuit et sans cloud.

### Pourquoi le mettre dans docker-compose ?

Jusqu'ici, le `docker-compose.yml` ne contenait que PostgreSQL. En ajoutant Ollama comme second service, on centralise toute l'infrastructure : un seul `docker compose up -d` démarre tout ce dont le système a besoin.

### Ce qu'il faut ajouter

**Fichier** : `docker-compose.yml`

Actuellement vous avez :

```yaml
services:
  postgres:
    # ... (déjà en place)

volumes:
  pgdata:
```

Ajouter le service `ollama` et son volume :

```yaml
services:
  postgres:
    # ... (inchangé)

  ollama:
    image: ollama/ollama:latest
    container_name: rag-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:11434/api/tags || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
  ollama_data:
```

### Explication ligne par ligne

| Ligne | Rôle |
|-------|------|
| `image: ollama/ollama:latest` | Image officielle Ollama depuis Docker Hub |
| `container_name: rag-ollama` | Nom fixe pour pouvoir faire `docker exec rag-ollama ...` |
| `ports: "11434:11434"` | Expose l'API Ollama sur le port standard 11434 |
| `volumes: ollama_data:/root/.ollama` | **Volume nommé** pour persister les modèles téléchargés. Sans ça, chaque `docker compose down` supprimerait les ~2 Go du modèle et il faudrait re-télécharger à chaque fois |
| `healthcheck: curl ...` | Vérifie qu'Ollama répond. Docker marque le conteneur comme `healthy` quand le check passe |

> **Le volume est important** : les modèles LLM sont volumineux (phi3.5 fait ~2 Go). Le volume `ollama_data` permet de les garder entre les redémarrages, exactement comme `pgdata` persiste les données PostgreSQL.

### Démarrer et vérifier

```bash
docker compose up -d          # démarre postgres + ollama
docker compose ps             # ollama doit être healthy
```

Puis télécharger un modèle (première fois uniquement, ~2 Go) :

```bash
docker exec rag-ollama ollama pull phi3.5
```

Vérifier qu'Ollama répond :

```bash
curl http://localhost:11434/api/tags
```

Vous devriez voir `phi3.5` dans la liste des modèles.

> **Note** : `phi3.5` est un modèle de ~3.8B paramètres de Microsoft. Il tourne sur CPU mais les réponses peuvent prendre 10-30 secondes. Si vous avez un GPU NVIDIA, Ollama l'utilisera automatiquement.

---

## Étape 1 : Ajouter les schémas dans `lib-schemas`

**Fichier** : `python/lib-schemas/lib_schemas/schemas.py`

Ajouter 3 nouveaux modèles Pydantic :

| Classe | Champs | Rôle |
|--------|--------|------|
| `GenerateRequest` | `question` (str, min 1 car), `top_k` (int, 1-50, défaut 5), `similarity_threshold` (float, 0-1, défaut 0) | Requête entrante |
| `Source` | `document_name`, `content`, `similarity_score` | Un document source cité dans la réponse |
| `GenerateResponse` | `question`, `answer`, `sources` (list[Source]), `model`, `retrieval_time_ms`, `generation_time_ms` | Réponse complète |

`GenerateRequest` ressemble à `SearchRequest` mais avec `question` au lieu de `query` — distinction pédagogique : l'utilisateur pose une **question**, le système fait une **recherche**.

`Source` est une version simplifiée de `SearchResult` : pas de `chunk_id` ni de `metadata`, juste ce qui est utile pour citer ses sources.

<details>
<summary>Indice : structure des modèles</summary>

```python
class GenerateRequest(BaseModel):
    """Request body for the generate endpoint."""

    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class Source(BaseModel):
    """A source document referenced in the generated answer."""

    document_name: str
    content: str
    similarity_score: float


class GenerateResponse(BaseModel):
    """Response from the generate endpoint."""

    question: str
    answer: str
    sources: list[Source]
    model: str
    retrieval_time_ms: float
    generation_time_ms: float
```

</details>

---

## Étape 2 : Créer le package `rag-generator`

### Structure

```
python/rag-generator/
├── rag_generator/
│   ├── __init__.py          # fourni
│   ├── main.py              # fourni (projen, ne pas modifier)
│   ├── task_inputs.py       # À IMPLÉMENTER
│   ├── app.py               # À IMPLÉMENTER
│   ├── api.py               # À IMPLÉMENTER
│   ├── dependencies.py      # À IMPLÉMENTER
│   ├── prompt.py            # À IMPLÉMENTER
│   └── routes/
│       ├── __init__.py      # fourni
│       ├── health.py        # À IMPLÉMENTER
│       └── generate.py      # À IMPLÉMENTER
├── tests/                    # fournis
├── pyproject.toml            # fourni
├── justfile                  # fourni
└── Dockerfile                # fourni
```

Installer les dépendances :

```bash
cd python/rag-generator && just install-dev
```

Exécuter les tests pour voir ce qui échoue :

```bash
just test   # tout doit être rouge au début
```

---

### Tâche 2.1 : `task_inputs.py` — Configuration

Même patron que `rag-retriever`, mais avec des champs différents.

| Champ | Type | Défaut | Rôle |
|-------|------|--------|------|
| `host` | str | `0.0.0.0` | Adresse d'écoute |
| `port` | int | `8001` | Port (différent du retriever !) |
| `retriever_url` | str | `http://localhost:8000` | URL du retriever |
| `ollama_url` | str | `http://localhost:11434` | URL d'Ollama |
| `ollama_model` | str | `phi3.5` | Modèle à utiliser |
| `top_k` | int | `5` | Nombre de chunks par défaut |
| `similarity_threshold` | float | `0.0` | Seuil de similarité par défaut |

> **Pas de `db_url`** ni de `embedding_model` : le generator ne touche pas à la base ni aux embeddings. C'est le retriever qui s'en charge.

<details>
<summary>Indice : patron BaseSettings</summary>

Inspirez-vous de `python/rag-retriever/rag_retriever/task_inputs.py`. C'est le même patron avec `SettingsConfigDict(cli_parse_args=True, cli_ignore_unknown_args=True)`. N'oubliez pas le singleton en fin de fichier :

```python
task_inputs = TaskInputs()  # type: ignore[call-arg, unused-ignore]
```

</details>

---

### Tâche 2.2 : `prompt.py` — Template de prompt

C'est le cœur de la stratégie RAG. Le prompt doit :

1. Donner un rôle à l'assistant ("answer based ONLY on the context")
2. Injecter les chunks récupérés comme contexte
3. Poser la question de l'utilisateur

**Fonction à implémenter** :

```python
def build_prompt(question: str, context_chunks: list[str]) -> str:
```

Les chunks doivent être séparés par `---` pour que le modèle distingue les différentes sources.

**Vérification** :

```bash
just test -- -k test_prompt   # 3 tests doivent passer
```

<details>
<summary>Indice : le template</summary>

```python
PROMPT_TEMPLATE = (
    "You are a helpful assistant. Answer the question based ONLY on the "
    "following context. If the context does not contain enough information "
    "to answer, say \"I don't have enough information to answer this "
    'question."\n\n'
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Answer:"
)

def build_prompt(question: str, context_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)
    return PROMPT_TEMPLATE.format(context=context, question=question)
```

</details>

---

### Tâche 2.3 : `dependencies.py` — Client HTTP partagé

Le generator fait des appels HTTP vers deux services (retriever + Ollama). On crée un `httpx.AsyncClient` partagé au démarrage, comme le retriever crée son engine DB et son client d'embedding.

**Fonctions à implémenter** :

| Fonction | Rôle |
|----------|------|
| `init_dependencies()` | Crée le `httpx.AsyncClient` avec un timeout de 120s |
| `shutdown_dependencies()` | Ferme le client proprement |
| `get_http_client()` | Retourne le client (raise RuntimeError si non initialisé) |
| `check_retriever_health()` | GET `{retriever_url}/health`, retourne `bool` |
| `check_ollama_health()` | GET `{ollama_url}/api/tags`, retourne `bool` |

> **Pourquoi 120s de timeout ?** Le LLM sur CPU peut prendre du temps. Un timeout trop court ferait échouer les requêtes.

<details>
<summary>Indice : patron global + init/shutdown</summary>

Le patron est le même que dans `rag_retriever/dependencies.py`, mais avec `httpx.AsyncClient` au lieu de `AsyncEngine` + `EmbeddingClient` :

```python
_http_client: httpx.AsyncClient | None = None

async def init_dependencies() -> None:
    global _http_client
    _http_client = httpx.AsyncClient(timeout=120.0)

async def shutdown_dependencies() -> None:
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
```

</details>

---

### Tâche 2.4 : `api.py` — Factory FastAPI

Même structure que `rag_retriever/api.py` :
- Un `lifespan` qui appelle `init_dependencies()` / `shutdown_dependencies()`
- Une factory `create_app()` qui monte les routers `health` et `generate`

Copiez et adaptez depuis le retriever. C'est ~30 lignes.

---

### Tâche 2.5 : `app.py` — Point d'entrée

Même patron que le retriever : afficher la config, puis `uvicorn.run(factory=True)`.

---

### Tâche 2.6 : `routes/health.py` — Probes de santé

Deux endpoints :
- `GET /health` → toujours `{"status": "ok"}`
- `GET /ready` → vérifie retriever ET Ollama, retourne 503 si l'un est down

Inspirez-vous de `rag_retriever/routes/health.py`, en remplaçant les checks DB/model par les checks retriever/Ollama.

---

### Tâche 2.7 : `routes/generate.py` — La route principale

C'est ici que tout se passe. La route `POST /generate` fait 4 choses :

```
Question de l'utilisateur
    ↓
1. POST {retriever_url}/search → SearchResponse
    ↓
2. Extraire les contenus des chunks → build_prompt()
    ↓
3. POST {ollama_url}/api/generate → réponse LLM
    ↓
4. Construire GenerateResponse avec sources + chronométrage
```

**Signature fournie** :

```python
@router.post("/generate")
async def generate(
    body: GenerateRequest,
    client: httpx.AsyncClient = Depends(get_http_client),  # noqa: B008
) -> GenerateResponse:
```

**API Ollama** : `POST /api/generate` avec le body JSON :

```json
{
    "model": "phi3.5",
    "prompt": "le prompt complet",
    "stream": false
}
```

La réponse contient un champ `"response"` avec le texte généré.

> **`stream: false`** : sans ce paramètre, Ollama envoie la réponse token par token en Server-Sent Events. On utilise `false` pour recevoir la réponse complète en une seule fois — beaucoup plus simple.

**Vérification** :

```bash
just test -- -k test_generate   # 2 tests doivent passer
just test                        # TOUS les tests doivent passer
just check-all                   # ruff + mypy clean
```

<details>
<summary>Indice 1 : appel au retriever</summary>

```python
search_resp = await client.post(
    f"{task_inputs.retriever_url}/search",
    json={
        "query": body.question,
        "top_k": body.top_k,
        "similarity_threshold": body.similarity_threshold,
    },
)
search_resp.raise_for_status()
search_data = SearchResponse(**search_resp.json())
```

On utilise `SearchResponse(**resp.json())` pour valider et structurer la réponse — c'est l'avantage d'avoir des schémas Pydantic partagés via `lib-schemas`.

</details>

<details>
<summary>Indice 2 : appel à Ollama</summary>

```python
ollama_resp = await client.post(
    f"{task_inputs.ollama_url}/api/generate",
    json={
        "model": task_inputs.ollama_model,
        "prompt": prompt,
        "stream": False,
    },
)
ollama_resp.raise_for_status()
answer = ollama_resp.json()["response"]
```

</details>

<details>
<summary>Indice 3 : construction des sources</summary>

Chaque `SearchResult` du retriever devient un `Source` dans la réponse :

```python
sources = [
    Source(
        document_name=r.document_name,
        content=r.content,
        similarity_score=r.similarity_score,
    )
    for r in search_data.results
]
```

</details>

---

## Étape 3 : Tester de bout en bout

### Terminal 1 : Infrastructure

```bash
docker compose up -d
docker exec rag-ollama ollama pull phi3.5   # première fois uniquement
```

### Terminal 2 : Retriever

```bash
just serve     # démarre le retriever sur :8000
```

### Terminal 3 : Generator

```bash
just generate  # démarre le generator sur :8001
```

### Terminal 4 : Tester

```bash
just ask "Quel type est Pikachu ?"
```

Ou avec curl :

```bash
curl -s -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"question": "Quel type est Pikachu ?"}' | python -m json.tool
```

La réponse devrait contenir :
- Un champ `answer` avec une réponse en langage naturel
- Un champ `sources` listant les chunks utilisés comme contexte
- Les temps de `retrieval_time_ms` et `generation_time_ms`

> **Patience** : la première requête peut prendre 20-30 secondes sur CPU (le modèle doit être chargé en mémoire). Les requêtes suivantes seront plus rapides (~10s).

---

## Vérification finale

```bash
cd python/rag-generator
just check-all    # ruff + mypy clean
just test          # 5 tests passent
```

---

## Récapitulatif

À la fin de cette étape, vous avez :

- [ ] Ollama fonctionnel avec le modèle `phi3.5` (`curl http://localhost:11434/api/tags`)
- [ ] Schémas `GenerateRequest`, `Source`, `GenerateResponse` dans `lib-schemas`
- [ ] Package `rag-generator` complet (task_inputs, prompt, dependencies, api, routes)
- [ ] `just generate` démarre le service sur `http://localhost:8001`
- [ ] `just ask "..."` retourne une réponse générée avec sources
- [ ] `just test` passe dans `python/rag-generator/`
- [ ] `just check-all` passe dans `python/rag-generator/`

---

## Pour aller plus loin

- **Changer de modèle** : `docker exec rag-ollama ollama pull llama3.2` puis relancer avec `--ollama-model llama3.2`
- **Prompt engineering** : modifier le template dans `prompt.py` et observer l'impact sur les réponses
- **Streaming** : remplacer `stream: false` par `stream: true` et utiliser les Server-Sent Events FastAPI
- **Évaluation** : comparer les réponses de différents modèles sur les mêmes questions
