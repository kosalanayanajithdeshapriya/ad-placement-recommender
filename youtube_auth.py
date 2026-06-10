"""
youtube_auth.py — Web-based OAuth2 for multi-user Streamlit on Render
"""

import os
import json
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

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
    raise FileNotFoundError("No Google credentials found. Set GOOGLE_CLIENT_SECRETS env variable.")

def get_redirect_uri():
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        return f"{render_url}/oauth2callback"
    return "http://localhost:8501/oauth2callback"

def build_flow():
    config = get_client_config()
    flow = Flow.from_client_config(
        config,
        scopes=SCOPES,
        redirect_uri=get_redirect_uri()
    )
    return flow

def get_credentials():
    # Already authenticated this session
    if "google_creds" in st.session_state:
        try:
            creds = Credentials.from_authorized_user_info(
                st.session_state["google_creds"], SCOPES
            )
            if creds.valid:
                return creds
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                st.session_state["google_creds"] = json.loads(creds.to_json())
                return creds
        except Exception:
            del st.session_state["google_creds"]

    # Check for OAuth callback code in URL
    params = dict(st.query_params)
    if "code" in params:
        try:
            flow = build_flow()
            flow.fetch_token(code=params["code"])
            creds = flow.credentials
            # Save BEFORE clearing params
            st.session_state["google_creds"] = json.loads(creds.to_json())
            st.session_state["just_logged_in"] = True
            st.query_params.clear()
            return creds
        except Exception as e:
            st.error(f"Login failed: {e}. Please try again.")
            st.query_params.clear()
            return None

    return None

def show_login_button():
    flow = build_flow()
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline"
    )
    return auth_url

def logout():
    for key in ["google_creds", "just_logged_in", "user_info"]:
        if key in st.session_state:
            del st.session_state[key]