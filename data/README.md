# 📦 Données — ShopVite

Les données utilisées pour construire l'index FAISS ont été **générées par Gemini** à partir des informations internes de ShopVite.

---

## Fichiers générés

| Fichier | Format | Contenu |
|---|---|---|
| `faq.json` | JSON | Questions/réponses clients fréquentes |
| `politique_de_retour.pdf` | PDF | Politique de retour et remboursement |
| `cgv.txt` | Texte brut | Conditions générales de vente |

---

## Aperçu du contenu

**`faq.json`** — liste de paires question/réponse couvrant la livraison, le paiement, le suivi de commande et le compte client.

**`politique_de_retour.pdf`** — document décrivant les délais de retour, les articles éligibles et la procédure de remboursement.

**`cgv.txt`** — texte brut des conditions générales : conditions d'achat, responsabilités, droit applicable et gestion des litiges.

---

## Pipeline d'ingestion

```
faq.json
politique_de_retour.pdf  ──▶  Chunking  ──▶  Embeddings  ──▶  faiss_index/
cgv.txt
```

Les fichiers sont chargés via LangChain (loaders adaptés à chaque format), découpés en chunks, transformés en vecteurs via `all-MiniLM-L6-v2`, puis stockés dans l'index FAISS persisté sur disque.

---

> ⚠️ Ces données sont synthétiques, générées par Gemini à des fins de démonstration. Elles ne constituent pas des CGV juridiquement contraignantes.
