# 🛒 ShopVite — RAG-powered Customer Support API

> A lightweight Retrieval-Augmented Generation (RAG) API that answers customer questions using your own product documentation — no hallucinations, every answer is grounded in your data.

🔗 **Live demo:** [huggingface.co/spaces/MISSAOUI/ShopVite](https://huggingface.co/spaces/MISSAOUI/ShopVite)  
📖 **Interactive docs:** [missaoui-shopvite-fastapi.hf.space/docs](https://missaoui-shopvite-fastapi.hf.space/docs)

---

## 🏗️ Architecture du pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                        INDEXING PHASE                           │
│               (offline — run once to build the index)          │
│                                                                 │
│  ┌──────────────────────┐       ┌──────────────────────────┐   │
│  │   📄 Source Docs     │──────▶│   ✂️  Text Chunking       │   │
│  │  PDF · FAQ · Docs    │       │  (overlapping windows)   │   │
│  └──────────────────────┘       └────────────┬─────────────┘   │
│                                              │                  │
│                                              ▼                  │
│                                 ┌──────────────────────────┐   │
│                                 │  🔢 Embedding Model       │   │
│                                 │  all-MiniLM-L6-v2 (HF)   │   │
│                                 └────────────┬─────────────┘   │
│                                              │                  │
│                                              ▼                  │
│                                 ┌──────────────────────────┐   │
│                                 │  🗄️  FAISS Vector Store   │   │
│                                 │  (persisted to disk)     │   │
│                                 └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        QUERY PHASE                              │
│               (online — every user request)                    │
│                                                                 │
│   👤 User Question                                              │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────┐                                       │
│  │  🔍 Retriever        │  top-k=3 most relevant chunks         │
│  │  (FAISS similarity)  │  + L2 distance scores                 │
│  └──────────┬───────────┘                                       │
│             │                                                   │
│             ▼                                                   │
│  ┌──────────────────────┐                                       │
│  │  📝 Prompt Template  │  Injects retrieved context            │
│  │  + Context Injection │  into a structured prompt             │
│  └──────────┬───────────┘                                       │
│             │                                                   │
│             ▼                                                   │
│  ┌──────────────────────┐                                       │
│  │  🤖 LLM              │  Mistral-medium via Mistral API       │
│  │  (mistral-medium)    │                                       │
│  └──────────┬───────────┘                                       │
│             │                                                   │
│             ▼                                                   │
│  ┌──────────────────────┐                                       │
│  │  ✅ Final Response   │  answer + sources + confidence score  │
│  └──────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Setup — 3 commands

```bash
# 1. Clone and install dependencies
git clone https://huggingface.co/spaces/MISSAOUI/ShopVite && cd ShopVite
pip install -r requirements.txt

# 2. Set your Mistral API key
export MISTRAL_API_KEY=your_key_here

# 3. Launch the API
uvicorn main:app --host 0.0.0.0 --port 7860
```

> **On Hugging Face Spaces:** skip step 2 — add `MISTRAL_API_KEY` under **Settings → Secrets** in your Space dashboard.

---

## 🧩 Choix techniques

| Composant | Choix | Justification |
|---|---|---|
| **Framework API** | FastAPI | Async-native, OpenAPI docs auto-générées, validation Pydantic intégrée |
| **Embedding model** | `all-MiniLM-L6-v2` | Excellent rapport qualité/vitesse sur CPU ; 384 dimensions ; modèle open-source |
| **Vector store** | FAISS (CPU) | Ultra-rapide pour les recherches par similarité ; pas de serveur requis ; fichier portable |
| **LLM** | Mistral-medium | Très bon en français ; coût maîtrisé ; compatible avec l'interface OpenAI |
| **Orchestration** | LangChain | Chaînes composables, intégration native FAISS + HuggingFace + OpenAI |
| **Hébergement** | HF Spaces (Docker) | Gratuit, CI/CD intégré, GPU/CPU disponibles, secrets sécurisés |

---

## 📬 Exemples de requêtes

### `POST /ask`

**Requête 1 — Question dans le contexte**

```json
{
  "question": "Quels sont vos délais de livraison ?"
}
```

```json
{
  "answer": "Nos délais de livraison standard sont de 3 à 5 jours ouvrés en France métropolitaine. La livraison express (24h) est disponible pour les commandes passées avant 14h.",
  "sources": ["faq.json, page 2", "CGV.txt, page 5"],
  "confidence": "high"
}
```

---

**Requête 2 — Question partiellement couverte**

```json
{
  "question": "Puis-je retourner un article soldé ?"
}
```

```json
{
  "answer": "Les articles soldés sont échangeables sous 14 jours mais ne sont pas remboursables, conformément à notre politique de retour.",
  "sources": ["politique_retour.pdf, page 1"],
  "confidence": "medium"
}
```

---

**Requête 3 — Question hors contexte**

```json
{
  "question": "Quelle est la capitale de l'Australie ?"
}
```

```json
{
  "answer": "Je suis désolé, cette information ne figure pas dans mes documents. Pour toute question spécifique, contactez notre support : support@shopvite.fr | 01 23 45 67 89 (lun-ven, 9h-18h).",
  "sources": [],
  "confidence": "out_of_context"
}
```

---

### `GET /health`

```json
{
  "status": "ok",
  "model": "mistral-medium",
  "vectorstore": "faiss_index"
}
```

---

## 📁 Structure du projet

```
ShopVite/
├── main.py                 # FastAPI app + RAG chain
├── prompt_engineering.py   # Prompt template builder
├── requirements.txt
├── Dockerfile
└── faiss_index/            # Pre-built vector store (commit this!)
    ├── index.faiss
    └── index.pkl
```

---

## 📄 Licence

MIT — free to use, modify, and deploy.
