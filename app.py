"""
Interface Streamlit :
- Auth MSAL device flow (affiche lien + code dans l'UI)
- Lecture et nettoyage des mails
- Assistant simple pour résumer les derniers mails
"""
from __future__ import annotations

import logging
import requests
import streamlit as st

from auth.msal_device_auth import MSALDeviceAuthManager
from app.ingestion.text_cleaner.text_cleaner_factory import TextCleanerFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_session_state() -> None:
    defaults = {
        "authenticated": False,
        "auth_manager": None,
        "access_token": None,
        "auth_message": None,
        "auth_flow": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def start_authentication() -> bool:
    """Lance le device flow et mémorise le message/code à afficher dans l'UI."""
    try:
        if st.session_state["auth_manager"] is None:
            st.session_state["auth_manager"] = MSALDeviceAuthManager()
        manager = st.session_state["auth_manager"]

        # Token déjà présent
        if manager.is_authenticated():
            st.session_state["authenticated"] = True
            st.session_state["access_token"] = manager.get_access_token()
            st.session_state["auth_flow"] = None
            st.session_state["auth_message"] = "✅ Authentification réussie (token en cache)"
            return True

        flow = manager.start_device_flow()
        st.session_state["auth_flow"] = flow
        st.session_state["auth_message"] = "🔐 Suivez les instructions ci-dessous."
        return False
    except Exception as exc:
        st.session_state["auth_message"] = f"❌ Erreur d'authentification : {exc}"
        logger.error("Auth error", exc_info=True)
        return False


def complete_authentication() -> bool:
    """Valide le device flow en utilisant le code saisi par l'utilisateur."""
    try:
        manager = st.session_state.get("auth_manager")
        flow = st.session_state.get("auth_flow")
        if manager is None or flow is None:
            st.session_state["auth_message"] = "❌ Aucun device flow actif."
            return False

        token = manager.complete_device_flow(flow)
        if token and "access_token" in token:
            st.session_state["authenticated"] = True
            st.session_state["access_token"] = token["access_token"]
            st.session_state["auth_flow"] = None
            st.session_state["auth_message"] = "✅ Authentification réussie !"
            return True
        st.session_state["auth_message"] = "❌ Aucun token reçu."
        return False
    except Exception as exc:
        st.session_state["auth_message"] = f"❌ Erreur d'authentification : {exc}"
        logger.error("Auth completion error", exc_info=True)
        return False


def fetch_emails(access_token: str, top: int = 10) -> list[dict]:
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    url = (
        "https://graph.microsoft.com/v1.0/me/messages"
        f"?$top={top}&$select=subject,from,receivedDateTime,toRecipients,ccRecipients,body"
    )
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 401:
        raise RuntimeError("reauth_required")
    resp.raise_for_status()
    data = resp.json() if resp.content else {}
    return data.get("value", []) if isinstance(data, dict) else []


def clean_email_body(cleaner, email: dict) -> str:
    body = (email.get("body") or {}).get("content", "") or ""
    meta = {
        "sender": (email.get("from", {}) or {}).get("emailAddress", {}).get("address", ""),
        "date": email.get("receivedDateTime", ""),
    }
    return cleaner.clean(body, metadata=meta)


def answer_query_on_emails(access_token: str, query: str, max_emails: int = 5) -> str:
    emails = fetch_emails(access_token, top=max_emails)
    cleaner = TextCleanerFactory.create("email")
    cleaned = []
    for mail in emails:
        cleaned.append(
            {
                "subject": mail.get("subject") or "(Sans sujet)",
                "sender": (mail.get("from", {}) or {}).get("emailAddress", {}).get("address", "Inconnu"),
                "date": mail.get("receivedDateTime", ""),
                "body": clean_email_body(cleaner, mail),
            }
        )
    lines = [f"- {m['date']} | {m['subject']} (de {m['sender']})" for m in cleaned]
    if "dernier" in query.lower() or "derniers" in query.lower():
        return "Voici vos derniers mails :\n" + "\n".join(lines)
    return "Je peux lister vos derniers mails :\n" + "\n".join(lines)


def main() -> None:
    st.set_page_config(page_title="Assistant IA Personnel", layout="wide")
    st.title("🤖 Assistant IA Personnel")
    initialize_session_state()

    # Messages d'état
    if st.session_state["auth_message"]:
        msg = st.session_state["auth_message"]
        if msg.startswith("❌"):
            st.error(msg)
        elif msg.startswith("✅"):
            st.success(msg)
        else:
            st.info(msg)

    # Bloc d'authentification
    if not st.session_state["authenticated"] or st.session_state["access_token"] is None:
        st.write("## Veuillez vous authentifier pour continuer")
        if st.button("🔐 Se connecter avec Microsoft 365", use_container_width=True):
            start_authentication()
            st.rerun()

        flow = st.session_state.get("auth_flow")
        if flow:
            st.warning(flow.get("message", ""))
            if st.button("✅ J'ai validé le code", use_container_width=True):
                if complete_authentication():
                    st.rerun()
                else:
                    st.error("Impossible de finaliser l'authentification.")

        st.info(
            "1) Clique sur Se connecter\n"
            "2) Ouvre le lien et saisis le code affiché\n"
            "3) Le token est sauvegardé pour les prochaines sessions"
        )
        return

    tab1, tab2, tab3 = st.tabs(["💬 Assistant IA", "📧 Emails", "📊 Statistiques"])

    # Assistant IA basique
    with tab1:
        st.write("### Posez une question sur vos derniers mails")
        user_query = st.text_input("Votre question :", key="assistant_query")
        if st.button("🔎 Interroger mes mails") and user_query:
            try:
                answer = answer_query_on_emails(st.session_state["access_token"], user_query, max_emails=5)
                st.success(answer)
            except RuntimeError as exc:
                if str(exc) == "reauth_required":
                    st.warning("Token expiré. Veuillez relancer la connexion.")
                    st.session_state["authenticated"] = False
                    st.session_state["access_token"] = None
                    st.session_state["auth_flow"] = None
                else:
                    st.error(f"Erreur : {exc}")
            except Exception as exc:
                st.error(f"Erreur : {exc}")

    # Listing mails nettoyés
    with tab2:
        st.write("### Vos Emails")
        num_emails = st.number_input("Nombre d'emails à charger", min_value=1, max_value=50, value=10)
        if st.button("📥 Charger mes emails"):
            try:
                emails = fetch_emails(st.session_state["access_token"], top=num_emails)
                if emails:
                    st.success(f"✅ {len(emails)} emails trouvés")
                    cleaner = TextCleanerFactory.create("email")
                    for i, email in enumerate(emails, 1):
                        subject = email.get("subject", "(Sans sujet)")
                        sender_email = (email.get("from", {}) or {}).get("emailAddress", {}).get("address", "Inconnu")
                        sender_name = (email.get("from", {}) or {}).get("emailAddress", {}).get("name", "Inconnu")
                        date = email.get("receivedDateTime", "")
                        cleaned_body = clean_email_body(cleaner, email)
                        to_list = [
                            r["emailAddress"].get("name", r["emailAddress"].get("address", ""))
                            for r in email.get("toRecipients", [])
                        ]
                        cc_list = [
                            r["emailAddress"].get("name", r["emailAddress"].get("address", ""))
                            for r in email.get("ccRecipients", [])
                        ]
                        with st.expander(f"**{i}. {subject}** — {sender_name or sender_email}"):
                            st.markdown(
                                f"**De :** {sender_name or sender_email}  \n"
                                f"**Date :** {date}  \n"
                                f"**A :** {', '.join(to_list) if to_list else 'N/A'}  \n"
                                f"**Cc :** {', '.join(cc_list) if cc_list else 'N/A'}  \n\n"
                                f"{cleaned_body}"
                            )
                else:
                    st.info("Aucun email trouvé")
            except RuntimeError as exc:
                if str(exc) == "reauth_required":
                    st.warning("Token expiré. Veuillez relancer la connexion.")
                    st.session_state["authenticated"] = False
                    st.session_state["access_token"] = None
                    st.session_state["auth_flow"] = None
                else:
                    st.error(f"Erreur : {exc}")
            except Exception as exc:
                st.error(f"Erreur : {exc}")

    with tab3:
        st.info("Statistiques à venir.")

    if st.button("🚪 Déconnexion"):
        mgr = st.session_state.get("auth_manager")
        if mgr:
            mgr.logout()
        st.session_state["authenticated"] = False
        st.session_state["access_token"] = None
        st.session_state["auth_flow"] = None
        st.session_state["auth_message"] = "✅ Déconnexion réussie"
        st.rerun()


if __name__ == "__main__":
    main()
