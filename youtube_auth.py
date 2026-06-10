"""
youtube_auth.py — OAuth2 using root redirect URI (no PKCE)
"""

import os
import json
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

def get_client_config():
    env_secret = os.getenv("GOOGLE_CLIENT_SECRETS")
    if env_secret:
        return json.loads(env_secret)
    if os.path.exists("client_secret.json"):
        with open("client_secret.json") as f:
            return json.load(f)
    raise FileNotFoundError("No Google credentials found.")

def get_redirect_uri():
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        return f"{render_url}/"
    return "http://localhost:8501/"

def build_flow():
    config = get_client_config()
    flow = Flow.from_client_config(
        config,
        scopes=SCOPES,
        redirect_uri=get_redirect_uri()
    )
    # Explicitly disable PKCE — google-auth-oauthlib 1.4.0 auto-enables it,
    # but Streamlit loses session state during the Google redirect so the
    # code_verifier cannot be persisted.
    flow.autogenerate_code_verifier = False
    flow.code_verifier = None
    return flow

def get_credentials():
    params = dict(st.query_params)

    # ── Handle OAuth callback ──
    if "code" in params:
        try:
            flow = build_flow()
            flow.fetch_token(
                code=params["code"],
                include_client_id=True
            )
            creds = flow.credentials
            st.session_state["google_creds"] = creds.to_json()
            st.query_params.clear()
            return creds
        except Exception as e:
            st.error(f"Login failed: {e}. Please try again.")
            st.query_params.clear()
            return None

    # ── Restore from session_state ──
    if "google_creds" in st.session_state:
        try:
            creds = Credentials.from_authorized_user_info(
                json.loads(st.session_state["google_creds"]), SCOPES
            )
            if creds.valid:
                return creds
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                st.session_state["google_creds"] = creds.to_json()
                return creds
        except Exception:
            del st.session_state["google_creds"]

    return None

def show_login_button():
    flow = build_flow()
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline",
        include_granted_scopes="true"
    )
    return auth_url

def logout():
    if "google_creds" in st.session_state:
        del st.session_state["google_creds"]