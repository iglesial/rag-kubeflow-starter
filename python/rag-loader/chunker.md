# Guide d'implémentation : `chunker.py`

## Pourquoi ce chunker ?

On veut couper un texte long en morceaux de taille max `chunk_size` pour les stocker dans une base vectorielle. Le problème : **où couper ?**

### Le dilemme

```
"Les pipelines ML automatisent l'entraînement. Kubeflow orchestre ces pipelines sur Kubernetes."
```

Si on coupe bêtement tous les 40 caractères :

```
chunk 1: "Les pipelines ML automatisent l'entraîn"   ← coupe un mot
chunk 2: "ement. Kubeflow orchestre ces pipelines "   ← commence au milieu d'une idée
```

C'est inutilisable pour la recherche sémantique — quand un utilisateur cherche "entraînement", il tombe sur un chunk tronqué.

### L'idée : couper au meilleur endroit possible

Un texte a une **hiérarchie naturelle** :

```
Paragraphe 1                          ← séparé par \n\n
  Ligne 1                             ← séparée par \n
    Phrase 1. Phrase 2.               ← séparées par ". "
      mot1 mot2 mot3                  ← séparés par " "
        caractères                    ← séparés par ""
```

On préfère toujours couper **au niveau le plus haut possible** :
- Entre deux paragraphes, c'est parfait (changement de sujet)
- Entre deux phrases, c'est bien (idée complète)
- Entre deux mots, c'est acceptable
- Entre deux caractères, c'est le dernier recours

C'est exactement l'ordre de `SEPARATORS = ["\n\n", "\n", ". ", " ", ""]`.

### L'algorithme en une phrase

**Essaie de couper sur `\n\n`. Si les morceaux sont encore trop gros, re-essaie sur `\n`. Encore trop gros ? sur `". "`. Puis `" "`. Puis caractère par caractère.**

C'est la récursion : chaque morceau trop grand est re-découpé avec le séparateur suivant.

### Et l'overlap ?

Une fois qu'on a nos morceaux propres, on les **fusionne** en chunks de taille max, et on fait chevaucher les chunks entre eux :

```
chunk 1: "Les pipelines ML automatisent l'entraînement."
chunk 2: "l'entraînement. Kubeflow orchestre ces pipelines."
          ^^^^^^^^^^^^^^
          overlap : le contexte de transition est dans les deux chunks
```

Pourquoi ? Parce qu'une requête utilisateur peut porter sur une idée **à cheval** entre deux chunks. L'overlap garantit qu'au moins un chunk contient l'idée complète.

### Résumé

| Étape | Fonction | Rôle |
|-------|----------|------|
| 1. Diviser | `_split_recursive` | Couper au meilleur séparateur, récursivement |
| 2. Fusionner | `_merge_with_overlap` | Regrouper les petits morceaux + ajouter le chevauchement |

C'est tout. Le reste c'est de la mécanique (rattacher le point de `". "`, gérer le texte vide, lever une erreur si overlap >= chunk_size).

---

## Objectif

Implémenter une fonction `chunk_text(text, chunk_size=512, chunk_overlap=64) -> list[str]` qui découpe un texte en morceaux (chunks) de taille contrôlée, avec recouvrement entre chunks consécutifs.

## Constante

```python
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]
```

Les séparateurs sont essayés **dans l'ordre** : paragraphe, ligne, phrase, mot, caractère.

## Règles déduites des tests

| Règle | Tests correspondants |
|-------|---------------------|
| Texte vide ou uniquement des espaces/sauts de ligne → `[]` | `test_empty_string`, `test_whitespace_only` |
| Texte plus court que `chunk_size` → un seul chunk tel quel | `test_short_text_single_chunk` |
| `chunk_overlap >= chunk_size` → lever `ValueError` | `test_overlap_ge_chunk_size_raises`, `test_overlap_greater_than_chunk_size_raises` |
| **Aucun chunk** ne doit dépasser `chunk_size` (sauf mot unique indivisible) | `test_no_chunk_exceeds_size`, `test_overlap_small_example` |
| Deux paragraphes courts → split sur `\n\n` | `test_two_paragraphs_split_on_double_newline` |
| Paragraphe long sans `\n` → split sur `". "` (phrases) | `test_long_paragraph_splits_on_sentence` |
| Pas de phrases → split sur `" "` (mots) | `test_splits_on_words_when_no_sentences` |
| Un mot unique plus long que `chunk_size` → le couper en morceaux par caractères, ne pas le supprimer | `test_single_long_word_returned_as_is` |
| Chunks consécutifs doivent **se chevaucher** : les derniers caractères du chunk N apparaissent au début du chunk N+1 | `test_overlap_between_chunks`, `test_overlap_small_example` |
| Sur un document réaliste (Markdown avec titres, paragraphes), tout le contenu original doit être présent dans les chunks | `test_real_document_chunking` |

## Architecture suggérée : 2 fonctions internes

### `_split_recursive(text, chunk_size, sep_idx)` — Diviser

1. Si `len(text) <= chunk_size` → retourner `[text]` (cas de base)
2. Prendre le séparateur à l'index `sep_idx` dans `SEPARATORS`
3. Cas spécial `""` (dernier séparateur) → découper caractère par caractère en tranches de `chunk_size`
4. `text.split(sep)` → si un seul morceau, le séparateur n'existe pas dans le texte → **récurser** avec `sep_idx + 1`
5. Sinon, pour chaque morceau : s'il tient dans `chunk_size`, le garder ; sinon **récurser** dessus avec le séparateur suivant
6. Attention : pour `". "`, le split mange le point — penser à le **rattacher**

### `_merge_with_overlap(segments, chunk_size, chunk_overlap)` — Fusionner et chevaucher

1. Parcourir les segments et les **concaténer** tant que la taille reste ≤ `chunk_size`
2. Quand un segment ferait dépasser la limite → finaliser le chunk courant, puis démarrer le suivant en reprenant les `chunk_overlap` derniers caractères du chunk précédent comme préfixe

### Conseil

Commencez par faire passer les tests simples (vide, court, ValueError), puis implémentez `_split_recursive` seul (sans overlap), et enfin ajoutez `_merge_with_overlap`.

---

## Exemples pas à pas

### 1. Split sur paragraphes (`\n\n`)

```
chunk_size=30, chunk_overlap=0

Texte : "Bonjour monde.\n\nDeuxième bloc."
                       ^^
                    séparateur \n\n

→ _split_recursive coupe sur "\n\n"
  segment 1: "Bonjour monde."     (15 cars ≤ 30 ✓)
  segment 2: "Deuxième bloc."     (14 cars ≤ 30 ✓)

→ _merge_with_overlap (overlap=0, pas de fusion nécessaire)

Résultat : ["Bonjour monde.", "Deuxième bloc."]
```

### 2. Fallback vers les phrases (`". "`)

```
chunk_size=35, chunk_overlap=0

Texte : "Phrase un ici. Phrase deux ici. Phrase trois ici."
         (49 cars > 35 → trop long, split sur "\n\n" ? non, absent)
         → split sur "\n" ? non, absent
         → split sur ". " ✓

  text.split(". ") → ["Phrase un ici", "Phrase deux ici", "Phrase trois ici."]
                       ⚠️ le point a disparu !

  Rattacher le "." :  ["Phrase un ici.", "Phrase deux ici.", "Phrase trois ici."]

→ _merge_with_overlap (overlap=0)
  "Phrase un ici."  (14 cars)
  + " " + "Phrase deux ici." = "Phrase un ici. Phrase deux ici." (31 cars ≤ 35 ✓) → fusionner
  + " " + "Phrase trois ici." = 49 cars > 35 → couper !

Résultat : ["Phrase un ici. Phrase deux ici.", "Phrase trois ici."]
```

### 3. Fallback vers les mots (`" "`)

```
chunk_size=12, chunk_overlap=0

Texte : "aa bb cc dd ee ff"
         (17 cars > 12)
         → "\n\n" ? non → "\n" ? non → ". " ? non
         → split sur " " ✓

  segments : ["aa", "bb", "cc", "dd", "ee", "ff"]

→ _merge_with_overlap
  "aa" + " " + "bb" = "aa bb"       (5 ≤ 12 ✓)
  + " " + "cc"       = "aa bb cc"    (8 ≤ 12 ✓)
  + " " + "dd"       = "aa bb cc dd" (11 ≤ 12 ✓)
  + " " + "ee"       = 14 > 12      → couper !

  chunk 1: "aa bb cc dd"
  "ee" + " " + "ff" = "ee ff"       (5 ≤ 12 ✓)

  chunk 2: "ee ff"

Résultat : ["aa bb cc dd", "ee ff"]
```

### 4. Avec overlap

```
chunk_size=12, chunk_overlap=5

Mêmes segments : ["aa", "bb", "cc", "dd", "ee", "ff"]

→ _merge_with_overlap
  chunk 1 : "aa bb cc dd"  (11 cars)
                   ^^^^^
                   tail = "cc dd" (5 derniers caractères)

  Nouveau chunk commence par l'overlap : "cc dd"
  "cc dd" + " " + "ee" = "cc dd ee" (8 ≤ 12 ✓)
  + " " + "ff"          = "cc dd ee ff" (11 ≤ 12 ✓)

  chunk 2 : "cc dd ee ff"

Résultat : ["aa bb cc dd", "cc dd ee ff"]
            ─────┘└─────
            overlap partagé : "cc dd"
```

### 5. Mot unique trop long (fallback `""`)

```
chunk_size=5, chunk_overlap=2

Texte : "abcdefghij"   (10 cars > 5)
         → "\n\n" ? non → "\n" ? non → ". " ? non → " " ? non
         → séparateur "" → découpe par tranches de chunk_size

  segments : ["abcde", "fghij"]

→ _merge_with_overlap
  "abcde" (5 ≤ 5 ✓) → chunk 1
  overlap = "de" (2 derniers cars)
  "de" + " " + "fghij" = 8 > 5 → overlap ne tient pas
  chunk 2 : "fghij"

Résultat : ["abcde", "fghij"]
           "".join() = "abcdefghij" → rien n'est perdu ✓
```

### 6. Récursion mixte (cas réaliste)

```
chunk_size=40, chunk_overlap=5

Texte :
"# Titre\n\nParagraphe un est assez long pour dépasser. Phrase courte."

→ split "\n\n"
  seg 1 : "# Titre"                                    (7 ≤ 40 ✓)
  seg 2 : "Paragraphe un est assez long pour dépasser. Phrase courte."
           (58 cars > 40 → récurser avec sep_idx+1)

  → split "\n" sur seg 2 ? non
  → split ". " sur seg 2 ✓
    ["Paragraphe un est assez long pour dépasser.", "Phrase courte."]
      (45 > 40 → récurser !)              (14 ≤ 40 ✓)

    → split " " sur "Paragraphe un est assez long pour dépasser."
      ["Paragraphe", "un", "est", "assez", "long", "pour", "dépasser."]

segments finaux : ["# Titre", "Paragraphe", "un", "est", "assez",
                   "long", "pour", "dépasser.", "Phrase courte."]

→ _merge_with_overlap (chunk_size=40, overlap=5)
  "# Titre Paragraphe un est assez long"  (37 ≤ 40 ✓)
  + " pour" = 42 > 40 → couper !

  chunk 1 : "# Titre Paragraphe un est assez long"
  overlap = " long"
  "long pour dépasser. Phrase courte."    (34 ≤ 40 ✓)

  chunk 2 : "long pour dépasser. Phrase courte."

Résultat : ["# Titre Paragraphe un est assez long",
            "long pour dépasser. Phrase courte."]
```
