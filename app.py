import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import secrets
import hashlib
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="MétalSuivi SaaS Enterprise", page_icon="🏗️", layout="wide")

# --- CONFIGURATION API PAYTECH ---
PAYTECH_API_KEY = st.secrets["PAYTECH_API_KEY"]
PAYTECH_SECRET_KEY = st.secrets["PAYTECH_API_SECRET"]
PAYTECH_URL = "https://paytech.sn/api/payment/request-payment" 
BASE_URL = "https://zunongroguhe-bit-metalsuivi-saas-app-hc0xsr.streamlit.app/"

# --- CSS ET DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #F4F8FA !important; font-family: 'Poppins', sans-serif !important; color: #0F2537 !important; }
    [data-testid="stSidebar"] { background-color: #1E2432 !important; }
    .lws-card { background: linear-gradient(135deg, #FF5E00 0%, #FF7A00 100%) !important; padding: 35px; border-radius: 16px; box-shadow: 0 10px 25px rgba(255, 94, 0, 0.25); margin-bottom: 25px; color: #FFFFFF !important; }
    .lws-title { font-size: 2.2rem !important; font-weight: 700 !important; color: #FFFFFF !important; }
    .lws-subtitle { font-size: 1.1rem !important; color: #FFFFFF !important; opacity: 0.95; }
    div.stButton > button:first-child { background: linear-gradient(135deg, #0F2537 0%, #1E3A52 100%) !important; color: white !important; padding: 12px 30px !important; border-radius: 30px !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DONNÉES ---
def get_db_connection():
    return sqlite3.connect("metalsuivi_saas.db", check_same_thread=False, timeout=10)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS licences (id INTEGER PRIMARY KEY AUTOINCREMENT, cle_licence TEXT UNIQUE, statut TEXT, date_expiration TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS entreprises (id INTEGER PRIMARY KEY AUTOINCREMENT, nom_entreprise TEXT, email TEXT UNIQUE, mot_de_passe TEXT, date_inscription TEXT, licence_active TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS projets (id INTEGER PRIMARY KEY AUTOINCREMENT, entreprise_id INTEGER, code_projet TEXT UNIQUE, nom_projet TEXT, client_nom TEXT, client_telephone TEXT, tonnage REAL, finition TEXT, date_creation TEXT, etape_actuelle TEXT, bat_status TEXT, bat_commentaire TEXT, liste_colisage TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS fil_actualite (id INTEGER PRIMARY KEY AUTOINCREMENT, code_projet TEXT, date_evenement TEXT, etape TEXT, commentaire TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- FONCTIONS LOGIQUES ---
def generer_nouvelle_licence(jours=30):
    conn = get_db_connection()
    c = conn.cursor()
    cle = f"LIC-{secrets.token_hex(2).upper()}"
    exp = (datetime.today() + timedelta(days=jours)).strftime('%Y-%m-%d')
    c.execute("INSERT INTO licences (cle_licence, statut, date_expiration) VALUES (?, 'disponible', ?)", (cle, exp))
    conn.commit()
    conn.close()
    return cle

def requete_paiement_paytech(item_name, price):
    headers = {"Accept": "application/json", "Content-Type": "application/json", "API_KEY": PAYTECH_API_KEY, "API_SECRET": PAYTECH_SECRET_KEY}
    payload = {
        "item_name": item_name, "item_price": price, "currency": "XOF", 
        "ref_command": f"CMD-{secrets.token_hex(4).upper()}", 
        "env": "live", "success_url": BASE_URL, "cancel_url": BASE_URL, "ipn_url": BASE_URL
    }
    try:
        res = requests.post(PAYTECH_URL, json=payload, headers=headers).json()
        return res.get("redirect_url") if res.get("success") == 1 else None
    except: return None

# --- SESSIONS & UI ---
if "connected_at" not in st.session_state: st.session_state["connected_at"] = None
if "entreprise_id" not in st.session_state: st.session_state["entreprise_id"] = None

with st.sidebar:
    menu = st.radio("Navigation", ["🏢 Espace Atelier (SaaS)", "🔐 Espace Suivi Client", "🛠️ Générateur Licences (Admin)"])
    if st.session_state["connected_at"]:
        if st.button("Déconnexion"): st.session_state.clear(); st.rerun()

# --- GESTION RETOUR PAIEMENT ---
if "status" in st.query_params and st.query_params["status"] == "success":
    st.balloons()
    st.success("🎉 Paiement validé ! Votre accès est activé.")
    st.query_params.clear()

# --- PAGES ---
if menu == "🏢 Espace Atelier (SaaS)":
    if not st.session_state["connected_at"]:
        tab1, tab2, tab3 = st.tabs(["🔑 Connexion", "📝 Création", "🛒 Abonnement"])
        with tab3:
            st.markdown("<div class='lws-card'><h3>Abonnement Pro</h3><p>Accédez à votre espace complet.</p></div>", unsafe_allow_html=True)
            if st.button("Payer 10 000 F CFA via PayTech"):
                url = requete_paiement_paytech("Abonnement Mensuel MetalSuivi", 10000)
                if url: st.link_button("Finaliser le paiement ici", url)
                else: st.error("Service indisponible.")
    else:
        st.write(f"Bienvenue, {st.session_state['connected_at']}")
        # Logique de gestion des chantiers...

elif menu == "🔐 Espace Suivi Client":
    st.title("Suivi de Chantier")
    code = st.text_input("Code de suivi (ex: MS-XXXX)")
    # Logique de recherche projet...

elif menu == "🛠️ Générateur Licences (Admin)":
    st.title("Admin - Générateur")
    if st.button("Générer une nouvelle clé"):
        st.code(generer_nouvelle_licence())
