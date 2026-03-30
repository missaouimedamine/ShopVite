import streamlit as st
import requests

API_URL = "http://localhost:8000"  # ← changer en prod

st.set_page_config(page_title="ShopVite Assistant", page_icon="🛒")
st.title("🛒 ShopVite — Assistant FAQ")
st.caption("Posez vos questions sur nos produits, livraisons et retours.")

# ── Vérification santé API ────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def check_health():
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

if not check_health():
    st.error("⚠️ API indisponible. Vérifiez que `api.py` est bien lancé.")
    st.stop()

# ── Historique ────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📄 Sources"):
                for s in msg["sources"]:
                    st.markdown(f"- `{s}`")

# ── Input ─────────────────────────────────────────────────────────────────────
CONFIDENCE_BADGE = {
    "high":           "🟢 Confiance élevée",
    "medium":         "🟡 Confiance moyenne",
    "low":            "🔴 Confiance faible",
    "out_of_context": "⚫ Hors contexte",
}

if question := st.chat_input("Votre question..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Recherche en cours..."):
            try:
                resp = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question},
                    timeout=30
                )
                resp.raise_for_status()
                data = resp.json()

                answer     = data["answer"]
                sources    = data.get("sources", [])
                confidence = data.get("confidence", "low")

                st.markdown(answer)
                st.caption(CONFIDENCE_BADGE.get(confidence, ""))

                if sources:
                    with st.expander("📄 Sources"):
                        for s in sources:
                            st.markdown(f"- `{s}`")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })

            except requests.exceptions.Timeout:
                st.error("⏱️ L'API met trop de temps à répondre.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Impossible de joindre l'API.")
            except Exception as e:
                st.error(f"❌ Erreur : {str(e)}")