"""
Interface Streamlit pour l'agent IA :
- Authentification MSAL Device Flow multi-utilisateur (cache par user)
- Lecture + nettoyage des emails via EmailTextCleaner
"""
from __future__ import annotations

import logging
import requests
import streamlit as st

from auth.msal_device_auth import MSALDeviceAuthManager
from app.ingestion.text_cleaner.email_text_cleaner import EmailTextCleaner

# ---------------------------------------------------------------------
# Configuration log
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------
def initialize_session_state() -> None:
    defaults = {
        "authenticated": False,
        "current_user_email": None,
        "current_user_id": None,
        "access_token": None,
        "auth_manager": MSALDeviceAuthManager(),
        "auth_flow": None,
        "auth_message": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------
# Auth helpers (device flow)
# ---------------------------------------------------------------------
def authenticate_new_user() -> None:
    """
    Démarre le device flow si pas déjà lancé, sinon réaffiche le message.
    Le flow + message sont stockés dans session_state.
    """
    manager = st.session_state["auth_manager"]
    if st.session_state.get("auth_flow") is None:
        message, flow = manager.initiate_device_flow()
        if flow is None:
            st.error("❌ Erreur lors de l'initialisation du device flow")
            return
        st.session_state["auth_flow"] = flow
        st.session_state["auth_message"] = message
    # Rien d'autre à faire ici : le message est affiché dans l'UI


def complete_device_flow() -> bool:
    """Valide le device flow courant et met à jour l'état d'auth."""
    manager = st.session_state["auth_manager"]
    flow = st.session_state.get("auth_flow")
    if flow is None:
        st.error("❌ Aucun device flow en cours")
        return False

    token = manager.acquire_token_by_flow(flow)
    if token:
        st.session_state["authenticated"] = True
        st.session_state["access_token"] = token
        st.session_state["current_user_email"] = manager.current_user_email
        st.session_state["current_user_id"] = manager.current_user_id
        st.session_state["auth_flow"] = None
        st.session_state["auth_message"] = None
        st.success(f"✅ Connecté en tant que {st.session_state['current_user_email']}")
        return True

    st.error("❌ Authentification échouée")
    return False


def login_cached_user(user_email: str) -> None:
    """Connexion silencieuse avec un utilisateur déjà en cache."""
    manager = st.session_state["auth_manager"]
    token = manager.get_cached_token(user_email)
    if token:
        st.session_state["authenticated"] = True
        st.session_state["access_token"] = token
        st.session_state["current_user_email"] = user_email
        st.session_state["current_user_id"] = manager.current_user_id
        st.success(f"✅ Connecté en tant que {user_email}")
        st.rerun()
    else:
        st.error(f"❌ Impossible de charger le token pour {user_email}")


def logout(user_email: str | None = None) -> None:
    """Déconnexion : supprime le cache de l'utilisateur et réinitialise l'état."""
    manager = st.session_state["auth_manager"]
    email = user_email or st.session_state.get("current_user_email")
    if email:
        manager.logout(email)
    st.session_state["authenticated"] = False
    st.session_state["current_user_email"] = None
    st.session_state["current_user_id"] = None
    st.session_state["access_token"] = None
    st.session_state["auth_flow"] = None
    st.session_state["auth_message"] = None
    st.success("✅ Déconnexion réussie")
    st.rerun()


# ---------------------------------------------------------------------
# UI: Emails
# ---------------------------------------------------------------------
def show_email_tab():
    """Onglet Emails (nécessite authentification)."""
    st.write("### 📧 Vos Emails")

    # Pas connecté -> montrer le device flow
    if not st.session_state["authenticated"]:
        st.warning("🔐 Vous devez vous authentifier pour accéder à vos emails")
        if st.button("🔐 Se connecter maintenant", use_container_width=True, type="primary"):
            authenticate_new_user()
        if st.session_state.get("auth_message"):
            st.info("📋 Instructions d'authentification")
            # lien cliquable si présent
            msg = st.session_state["auth_message"]
            st.markdown(
                msg.replace(
                    "https://microsoft.com/devicelogin",
                    "[https://microsoft.com/devicelogin](https://microsoft.com/devicelogin)",
                )
            )
            if st.button("✅ J'ai terminé", key="complete_flow_tab2", use_container_width=True):
                complete_device_flow()
        return

    # Chargement des emails
    col1, col2 = st.columns(2)
    with col1:
        num_emails = st.number_input("Nombre d'emails à charger:", min_value=1, max_value=50, value=10)

    with col2:
        if st.button("📥 Charger mes emails", use_container_width=True):
            try:
                headers = {
                    "Authorization": f"Bearer {st.session_state['access_token']}",
                    "Content-Type": "application/json",
                }
                with st.spinner(f"Chargement de {num_emails} emails..."):
                    response = requests.get(
                        f"https://graph.microsoft.com/v1.0/me/messages?$top={num_emails}"
                        "&$select=subject,from,receivedDateTime,toRecipients,ccRecipients,body",
                        headers=headers,
                    )
                if response.status_code == 200:
                    emails = response.json().get("value", [])
                    if emails:
                        st.success(f"✅ {len(emails)} emails trouvés")
                        cleaner = EmailTextCleaner()
                        for i, email in enumerate(emails, 1):
                            subject = email.get("subject", "(Sans sujet)")
                            sender_email = email.get("from", {}).get("emailAddress", {}).get("address", "")
                            sender_name = email.get("from", {}).get("emailAddress", {}).get("name", "Inconnu")
                            date = email.get("receivedDateTime", "")
                            body = email.get("body", {}).get("content", "")
                            body_type = email.get("body", {}).get("contentType", "html")
                            to_recipients = [
                                r["emailAddress"].get("name", r["emailAddress"].get("address", ""))
                                for r in email.get("toRecipients", [])
                            ]
                            cc_recipients = [
                                r["emailAddress"].get("name", r["emailAddress"].get("address", ""))
                                for r in email.get("ccRecipients", [])
                            ]
                            cleaned = cleaner.clean_email(
                                subject=subject,
                                sender=sender_email,
                                sender_name=sender_name,
                                date=date,
                                to_recipients=to_recipients,
                                cc_recipients=cc_recipients,
                                body=body,
                                body_type=body_type,
                            )
                            with st.expander(f"**{i}. {cleaned['subject']}** — {cleaned['sender_name']}"):
                                cleaned_str_only = {k: v for k, v in cleaned.items() if isinstance(v, str)}
                                st.markdown(cleaner.format_for_display(cleaned_str_only))
                    else:
                        st.info("ℹ️ Aucun email trouvé")
                else:
                    st.error(f"❌ Erreur {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"❌ Erreur lors du chargement: {e}")
                logger.error(f"Email loading error: {e}", exc_info=True)


# ---------------------------------------------------------------------
# UI: Connexion / gestion utilisateurs
# ---------------------------------------------------------------------
def show_users_tab():
    """Onglet de gestion des utilisateurs (liste des caches)."""
    st.write("### 👤 Connexion / Utilisateurs")
    users = st.session_state["auth_manager"].get_all_cached_users()

    if users:
        st.write("**👥 Utilisateurs enregistrés :**")
        cols = st.columns(min(len(users), 3))
        for idx, user in enumerate(users):
            with cols[idx % 3]:
                st.markdown(f"**{user['name']}**")
                st.caption(user["email"])
                if st.button("🔄 Connexion", use_container_width=True, key=f"user_{user['email']}"):
                    login_cached_user(user["email"])
        st.divider()
        st.write("**➕ Nouveau compte :**")
        if st.button("Se connecter avec un autre compte", use_container_width=True, type="primary"):
            authenticate_new_user()
    else:
        st.info("Aucun utilisateur enregistré.")
        if st.button("🔐 Se connecter avec Microsoft 365", use_container_width=True, type="primary"):
            authenticate_new_user()

    if st.session_state.get("auth_message"):
        st.warning("### 🔗 Instructions d'authentification")
        msg = st.session_state["auth_message"]
        st.markdown(
            msg.replace(
                "https://microsoft.com/devicelogin",
                "[https://microsoft.com/devicelogin](https://microsoft.com/devicelogin)",
            )
        )
        if st.button("✅ J'ai terminé", key="complete_flow_tab3", use_container_width=True):
            complete_device_flow()


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Assistant IA Personnel", layout="wide")
    st.title("🤖 Assistant IA Personnel")
    initialize_session_state()

    # En-tête (si connecté)
    if st.session_state["authenticated"]:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"### Bienvenue, {st.session_state['current_user_email']} !")
            st.caption(f"User ID: {st.session_state.get('current_user_id', '')}")
        with col2:
            if st.button("🔄 Changer d'utilisateur", use_container_width=True):
                logout()
        with col3:
            if st.button("🚪 Déconnexion", use_container_width=True):
                logout()
        st.divider()
    else:
        st.write("### 👋 Bienvenue !")
        st.info("Vous pouvez naviguer librement. Authentification requise uniquement pour accéder aux emails.")
        st.divider()

    tab1, tab2, tab3 = st.tabs(["💬 Assistant IA", "📧 Emails", "👥 Connexion"])

    with tab1:
        st.write("### 💬 Assistant IA")
        st.info("Fonctionnalité à venir...")
        user_input = st.text_input("Posez une question :", key="user_input")
        if user_input:
            st.info(f"Vous avez demandé : {user_input}")
            st.warning("L'agent IA n'est pas encore connecté.")

    with tab2:
        show_email_tab()

    with tab3:
        show_users_tab()


if __name__ == "__main__":
    main()
