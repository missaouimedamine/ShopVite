import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
from prompt_engineering import build_prompt

# ── État global ───────────────────────────────────────────────────────────────
rag_chain = None
retriever = None
load_dotenv()  # ← charge le fichier .env

# ── Helper format docs ────────────────────────────────────────────────────────
def format_docs(docs) -> str:
    """Convertit les documents récupérés en texte pour le prompt."""
    return "\n\n".join(
        f"[Source: {os.path.basename(doc.metadata.get('source', 'Inconnue'))}]\n{doc.page_content}"
        for doc in docs
    )

def extract_sources(docs) -> list[str]:
    """Formate les sources depuis les métadonnées des documents."""
    sources = []
    seen = set()
    for doc in docs:
        source = doc.metadata.get("source", "Inconnue")
        page   = doc.metadata.get("page")
        label  = (
            f"{os.path.basename(source)}, page {page + 1}"
            if page is not None
            else os.path.basename(source)
        )
        if label not in seen:
            sources.append(label)
            seen.add(label)
    return sources

def get_confidence(docs_with_scores: list) -> str:
    """Calcule le niveau de confiance selon les scores FAISS (distance L2)."""
    if not docs_with_scores:
        return "low"
    avg_score = sum(s for _, s in docs_with_scores) / len(docs_with_scores)
    if avg_score < 0.4:
        return "high"
    elif avg_score < 0.8:
        return "medium"
    return "low"


# ── Chargement au démarrage ───────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_chain, retriever

    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    vectorstore = FAISS.load_local(
        "faiss_index",
        embeddings=embedding,
        allow_dangerous_deserialization=True
    )

    


    llm = ChatOpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.getenv("MISTRAL_API_KEY"),
    model_name="mistral-medium"
)

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # ✅ FIX : retriever | format_docs (via RunnableLambda) pour convertir les
    #          documents en texte avant de les injecter dans le prompt
    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough()
        }
        | build_prompt()
        | llm
        | StrOutputParser()
    )

    print("✅ RAG chain chargée et prête.")
    yield
    print("🛑 Arrêt de l'API.")


# ── Application FastAPI ───────────────────────────────────────────────────────
app = FastAPI(
    title="ShopVite RAG API",
    version="1.0.0",
    lifespan=lifespan
)


# ── Schémas ───────────────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: str  # "high" | "medium" | "low" | "out_of_context"


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG chain non initialisée.")
    return {
        "status": "ok",
        "model": "mistral-medium",
        "vectorstore": "faiss_index"
    }


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest):
    question = body.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question trop longue (max 500 caractères).")

    # Récupérer les docs et leurs scores FAISS
    docs_with_scores = retriever.vectorstore.similarity_search_with_score(question, k=3)
    docs    = [doc for doc, _ in docs_with_scores]
    sources = extract_sources(docs)

    # Générer la réponse via la chaîne RAG
    try:
        answer = rag_chain.invoke(question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur LLM : {str(e)}")

    # Détecter question hors contexte
    if "HORS_CONTEXTE" in answer:
        return AskResponse(
            answer=(
                "Je suis désolé, cette information ne figure pas dans mes documents. "
                "Pour toute question spécifique, contactez notre support : "
                "support@shopvite.fr | 01 23 45 67 89 (lun-ven, 9h-18h)."
            ),
            sources=[],
            confidence="out_of_context"
        )

    confidence = get_confidence(docs_with_scores)

    return AskResponse(
        answer=answer,
        sources=sources,
        confidence=confidence
    )