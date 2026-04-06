# Guide d'implémentation : `reader.py`

## Pourquoi un reader ?

Le reader est la **première étape** du pipeline RAG : avant de découper le texte en chunks et de le vectoriser, il faut le **lire depuis le disque**.

### Le problème

On a un dossier `data/documents/` avec des fiches Pokédex en Markdown et d'autres fichiers :

```
data/documents/
├── 001-bulbizarre.md
├── 004-salameche.md
├── 007-carapuce.md
├── schema.png
└── rapport.pdf
```

On ne veut traiter que les fichiers Markdown (`.md`). Les images, PDF et autres doivent être ignorés silencieusement.

### Ce qu'on veut en sortie

Pour chaque fichier Markdown, un dictionnaire avec :

```python
{
    "document_name": "001-bulbizarre.md",     # nom du fichier (pas le chemin complet)
    "content": "# Bulbizarre\n\nType...",     # texte brut du fichier
    "metadata": {
        "file_size": 1024,                    # taille en octets
        "extension": ".md"                    # extension du fichier
    }
}
```

Le `document_name` servira plus tard d'identifiant unique dans la base pgvector (avec le `chunk_index`) pour faire les upserts.

---

## Objectif

Implémenter une fonction `read_documents(input_dir: str) -> list[dict[str, object]]` qui lit tous les fichiers `.md` d'un dossier et retourne leur contenu avec métadonnées.

## Constante

```python
SUPPORTED_EXTENSIONS = {".md"}
```

## Règles déduites des tests

| Règle | Tests correspondants |
|-------|---------------------|
| Seuls les fichiers `.md` sont lus | `test_reads_md` |
| Les fichiers `.png`, `.pdf`, etc. sont ignorés | `test_ignores_non_text_files` |
| Le contenu est lu fidèlement (texte brut, sauts de ligne préservés) | `test_document_content` |
| Chaque document a un champ `metadata` avec `file_size` (int > 0) et `extension` | `test_document_metadata` |
| Un dossier vide retourne `[]` | `test_empty_directory` |
| Un chemin inexistant lève `FileNotFoundError` avec "does not exist" dans le message | `test_nonexistent_directory` |
| Un fichier avec BOM UTF-8 est lu sans le BOM dans le contenu | `test_utf8_bom` |
| Plusieurs fichiers `.md` sont tous lus | `test_two_md_files` |

## Signature

```python
def read_documents(input_dir: str) -> list[dict[str, object]]:
```

## Étapes d'implémentation

1. **Valider le dossier** — Convertir `input_dir` en `Path`. Vérifier qu'il existe (`FileNotFoundError`) et que c'est un dossier (`NotADirectoryError`).

2. **Lister les fichiers** — Parcourir le dossier (non récursif), ne garder que les fichiers dont l'extension est dans `SUPPORTED_EXTENSIONS`. Trier par nom pour un ordre déterministe.

3. **Lire chaque fichier** — Construire le dictionnaire avec `document_name` (nom du fichier seul, pas le chemin), `content` et `metadata`.

4. **Retourner la liste** — Liste vide si aucun fichier trouvé.

## Exemple pas à pas

```
input_dir = "data/documents"

Contenu du dossier :
  001-bulbizarre.md  (312 octets)  "# Bulbizarre\n\nType : Plante/Poison..."
  004-salameche.md   (298 octets)  "# Salamèche\n\nType : Feu..."
  schema.png         (6 octets)    données binaires

→ Étape 1 : data/documents existe et est un dossier ✓

→ Étape 2 : lister et filtrer
  schema.png        → extension .png → ignoré
  001-bulbizarre.md → extension .md  → gardé
  004-salameche.md  → extension .md  → gardé

  Tri par nom : [001-bulbizarre.md, 004-salameche.md]

→ Étape 3 : lire chaque fichier

  001-bulbizarre.md → {
      "document_name": "001-bulbizarre.md",
      "content": "# Bulbizarre\n\nType : Plante/Poison...",
      "metadata": {"file_size": 312, "extension": ".md"}
  }

  004-salameche.md → {
      "document_name": "004-salameche.md",
      "content": "# Salamèche\n\nType : Feu...",
      "metadata": {"file_size": 298, "extension": ".md"}
  }

→ Résultat : [dict_bulbizarre, dict_salameche]
```

## Conseil

C'est la fonction la plus simple du projet (~25 lignes). Commencez par les validations (chemin inexistant, pas un dossier), puis le parcours avec filtre, puis la lecture.
