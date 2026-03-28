# RAG Kubeflow — Starter Template

Système RAG (Retrieval-Augmented Generation) avec FastAPI, PostgreSQL+pgvector et Kubeflow Pipelines.

## Démarrage rapide

```bash
# 1. Installer les outils (voir course/setup-guide.md)
# 2. Démarrer PostgreSQL
docker compose up -d

# 3. Installer les dépendances du premier package
cd python/rag-loader && just install-dev

# 4. Lancer les tests (ils échoueront — c'est normal !)
just test
```

## Structure

```
python/
├── lib-schemas/       # Schémas Pydantic partagés (fourni)
├── lib-embedding/     # Client d'embedding (fourni)
├── lib-orm/           # ORM asynchrone (fourni)
├── rag-loader/        # À implémenter (Session 1)
├── rag-embedder/      # À implémenter (Session 2)
├── rag-retriever/     # À implémenter (Session 2)
└── rag-pipeline/      # À implémenter (Session 3)
```

## Guides de session

- [Guide d'installation](course/setup-guide.md)
- [Session 1 — Fondations](course/session-1.md)
- [Session 2 — Embedding et API](course/session-2.md)
- [Session 3 — Orchestration Kubernetes](course/session-3.md)

## Commandes utiles

```bash
just --list            # voir toutes les recettes
just load              # exécuter le loader
just embed             # exécuter l'embedder
just pipeline          # load + embed
just serve             # démarrer l'API (http://localhost:8000)
just query "question"  # interroger l'API
just test-all          # tests de tous les packages
just check-all         # lint + typecheck
just e2e               # test d'intégration
```
