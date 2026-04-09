# Guide d'implémentation : Améliorer le workflow GitHub Actions

## Objectif

Vous disposez d'un workflow GitHub Actions (`.github/workflows/test-lib-embedding.yml`) qui teste le package `lib-embedding`. Il fonctionne, mais il a deux faiblesses :

1. **Le modèle d'embedding (~90 Mo) est re-téléchargé à chaque exécution** — c'est lent et gaspille de la bande passante
2. **Le rapport de couverture est invisible** — pytest affiche la couverture dans les logs, mais personne ne la consulte et rien n'empêche de merger du code non testé

Votre mission : améliorer ce workflow pour résoudre ces deux problèmes.

---

## Le workflow de départ

**Fichier** : `.github/workflows/test-lib-embedding.yml`

```yaml
name: Test lib-embedding

on:
  push:
    paths:
      - "python/lib-embedding/**"
  pull_request:
    paths:
      - "python/lib-embedding/**"

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: python/lib-embedding
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v6

      - name: Install dependencies
        run: uv sync --group dev

      - name: Install pre-commit
        run: pip install pre-commit
        working-directory: ${{ github.workspace }}

      - name: Run pre-commit
        run: pre-commit run --files $(git ls-files 'python/lib-embedding/')
        working-directory: ${{ github.workspace }}

      - name: Run tests
        run: uv run pytest
```

---

## Étape 1 : Comprendre le workflow existant

Avant de modifier, il faut comprendre. Relisez le fichier et répondez à ces questions :

| Question | Réponse attendue |
|----------|-----------------|
| Quand le workflow se déclenche-t-il ? | Sur `push` et `pull_request`, uniquement si des fichiers dans `python/lib-embedding/` changent |
| Pourquoi `paths` ? | Pour ne pas lancer les tests d'embedding quand on modifie le loader ou le retriever |
| Que fait `defaults.run.working-directory` ? | Tous les `run` s'exécutent dans `python/lib-embedding/` par défaut |
| Pourquoi `astral-sh/setup-uv@v6` ? | Installe `uv` sur le runner — pas besoin d'installer Python séparément, `uv` le fait via `uv sync` |
| Que fait `uv sync --group dev` ? | Installe les dépendances de production ET de développement (pytest, ruff, mypy…) |
| Pourquoi pre-commit utilise `working-directory: ${{ github.workspace }}` ? | Pre-commit doit s'exécuter à la racine du repo (il lit `.pre-commit-config.yaml` qui est à la racine) |
| Que fait `git ls-files 'python/lib-embedding/'` ? | Liste uniquement les fichiers trackés par git dans ce dossier — pre-commit ne vérifie que ceux-là |

### Ce qui se passe côté couverture

Le `pyproject.toml` de `lib-embedding` contient :

```toml
[tool.pytest.ini_options]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=lib_embedding",
]
```

Donc `uv run pytest` lance automatiquement `--cov=lib_embedding`. Le rapport s'affiche dans le terminal… mais qui va lire les logs d'une CI pour vérifier la couverture ?

---

## Étape 2 : Ajouter le cache du modèle HuggingFace

### Pourquoi ?

Quand pytest importe `lib_embedding`, le constructeur `EmbeddingClient("all-MiniLM-L6-v2")` télécharge le modèle depuis HuggingFace Hub. Ça fait ~90 Mo à chaque exécution du workflow.

```
Sans cache : checkout → install → download modèle (30s) → tests
Avec cache : checkout → install → cache hit (1s) → tests
```

### Ce qu'il faut savoir

- La documentation de `actions/cache@v4` est ici : https://github.com/actions/cache
- Sur Linux (et donc sur les runners `ubuntu-latest`), HuggingFace stocke les modèles téléchargés dans `~/.cache/huggingface/`
- Sur Windows, le chemin équivalent est `%USERPROFILE%\.cache\huggingface\` — vous pouvez vérifier en local que le modèle `all-MiniLM-L6-v2` s'y trouve après avoir lancé `just test` dans `python/lib-embedding/`

### Ce qu'il faut faire

En vous appuyant sur la documentation de `actions/cache@v4`, ajoutez un step qui **persiste le dossier du modèle** entre les exécutions du workflow.

Réfléchissez à :
- **Quel dossier** cacher ? (vous avez l'info ci-dessus)
- **Quelle clé** utiliser ? Le modèle ne change jamais — une clé fixe suffit
- **Où placer** le step ? Le cache doit être restauré **avant** que le modèle soit utilisé

### Vérification

Après avoir poussé cette modification :

1. **Premier run** : le step affiche `Cache not found for input keys: hf-all-MiniLM-L6-v2`. Les tests téléchargent le modèle. À la fin du job, le cache est sauvegardé.
2. **Deuxième run** : le step affiche `Cache restored from key: hf-all-MiniLM-L6-v2`. Pas de téléchargement, les tests sont plus rapides.

Comparez le temps du step `Run tests` entre les deux runs pour voir la différence.

<details>
<summary>Indice : placement dans le workflow</summary>

Le step de cache doit être ajouté **après** l'installation des dépendances et **avant** les tests :

```yaml
      - name: Install dependencies
        run: uv sync --group dev

      # ← ICI
      - name: Cache HuggingFace models
        uses: actions/cache@v4
        with:
          path: ~/.cache/huggingface
          key: hf-all-MiniLM-L6-v2

      - name: Run tests
        run: uv run pytest
```

</details>

---

## Étape 3 : Ajouter le rapport de couverture

Deux améliorations indépendantes. Faites-les dans l'ordre.

### 3a : Seuil minimum de couverture

On veut que le workflow **échoue** si la couverture descend en dessous d'un seuil. C'est un filet de sécurité : impossible de merger du code non testé.

**Ce qu'il faut faire** : modifier le step `Run tests` pour ajouter `--cov-fail-under=80` :

```yaml
      - name: Run tests
        run: uv run pytest --cov-fail-under=80
```

Si la couverture est inférieure à 80%, pytest retourne un code d'erreur et le workflow passe en rouge.

> **Pourquoi 80% ?** C'est un seuil pragmatique. 100% est irréaliste (certaines branches sont difficiles à tester). 80% force à tester le code critique sans bloquer sur les cas limites.

### 3b : Rapport HTML en artefact

Le terminal affiche un tableau résumé, mais pour savoir **quelles lignes** ne sont pas couvertes, il faut le rapport HTML.

**Ce qu'il faut faire** :

1. Ajouter `--cov-report=html` au step de test pour générer le rapport
2. Ajouter un step `actions/upload-artifact@v4` pour le rendre téléchargeable

Le rapport est généré dans le dossier `htmlcov/` par défaut.

**Vérification** :

1. Poussez la modification
2. Dans GitHub → Actions → le run du workflow → section "Artifacts" en bas
3. Téléchargez l'artefact, ouvrez `htmlcov/index.html` dans votre navigateur
4. Naviguez dans les fichiers pour voir quelles lignes sont couvertes (vert) ou non (rouge)

<details>
<summary>Indice : les deux steps à ajouter/modifier</summary>

```yaml
      - name: Run tests
        run: uv run pytest --cov-fail-under=80 --cov-report=html --cov-report=term

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: python/lib-embedding/htmlcov/
```

**Points importants** :
- `--cov-report=term` : garde l'affichage dans les logs (sinon `--cov-report=html` le remplace)
- `if: always()` : uploade le rapport **même si les tests échouent** — c'est justement quand ça échoue qu'on veut voir la couverture
- `path` : chemin **depuis la racine du repo** (pas relatif au `working-directory`)

</details>

---

## Workflow final attendu

Une fois les trois modifications faites, votre workflow devrait ressembler à ceci :

<details>
<summary>Voir le workflow complet</summary>

```yaml
name: Test lib-embedding

on:
  push:
    paths:
      - "python/lib-embedding/**"
  pull_request:
    paths:
      - "python/lib-embedding/**"

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: python/lib-embedding
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v6

      - name: Install dependencies
        run: uv sync --group dev

      - name: Install pre-commit
        run: pip install pre-commit
        working-directory: ${{ github.workspace }}

      - name: Run pre-commit
        run: pre-commit run --files $(git ls-files 'python/lib-embedding/')
        working-directory: ${{ github.workspace }}

      - name: Cache HuggingFace models
        uses: actions/cache@v4
        with:
          path: ~/.cache/huggingface
          key: hf-all-MiniLM-L6-v2

      - name: Run tests
        run: uv run pytest --cov-fail-under=80 --cov-report=html --cov-report=term

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: python/lib-embedding/htmlcov/
```

</details>

---

## Vérification

Poussez vos changements sur une branche et ouvrez une Pull Request :

```bash
git checkout -b feat/ci-improvements
git add .github/workflows/test-lib-embedding.yml
git commit -m "ci: add model cache and coverage report"
git push -u origin feat/ci-improvements
```

Dans GitHub, vérifiez :

- [ ] Le workflow se déclenche sur la PR
- [ ] Le step "Cache HuggingFace models" apparaît (cache miss au premier run)
- [ ] Les tests passent avec le rapport de couverture dans les logs
- [ ] L'artefact "coverage-report" est téléchargeable dans la page du workflow
- [ ] Au deuxième run, le cache est restauré (cache hit)

---

## Pour aller plus loin

- **Cache uv** : `astral-sh/setup-uv@v6` supporte `enable-cache: true` pour cacher les dépendances Python aussi
- **Badge de couverture** : ajouter un badge dans le README avec le pourcentage de couverture
- **Matrice de versions** : tester sur plusieurs versions de Python avec `strategy.matrix`
- **Commenter la PR** : utiliser une action comme `orgoro/coverage` pour poster le rapport de couverture en commentaire sur la PR
