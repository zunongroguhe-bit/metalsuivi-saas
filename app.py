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
# ATTENTION : Allez dans Settings > Secrets de votre app Streamlit et ajoutez :
# PAYTECH_API_KEY = "votre_cle_api"
# PAYTECH_API_SECRET = "votre_cle_secret"
PAYTECH_API_KEY = st.secrets["PAYTECH_API_KEY"]
PAYTECH_SECRET_KEY = st.secrets["PAYTECH_API_SECRET"]
PAYTECH_URL = "https://paytech.sn/api/payment/request-payment" 
CALLBACK_URL = "https://zunongroguhe-bit-metalsuivi-saas-app-hc0xsr.streamlit.app/"

# --- DESIGN GRAPHIQUE (LWS STYLE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: #F4F8FA !important; font-family: 'Poppins', sans-serif !important; color: #0F2537 !important; }
    [data-testid="stSidebar"] { background-color: #1E2432 !important; }
    .lws-card { background: linear-gradient(135deg, #FF5E00 0%, #FF7A00 100%) !important; padding: 35px; border-radius: 16px; box-shadow: 0 10px 25px rgba(255, 94, 0, 0.25); margin-bottom: 25px; color: #FFFFFF !important; }
    .lws-title { font-size: 2.2rem !important; font-weight: 700 !important; color: #FFFFFF !important; }
    .lws-subtitle { font-size: 1.1rem !important; color: #FFFFFF !important; opacity: 0.95; }
    div.stButton > button:first-child { background: linear-gradient(135deg, #0F2537 0%, #1E3A52 100%) !important; color: white !important; border-radius: 30px !important; }
    .metal-card-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
    .metal-card { background: linear-gradient(135deg, #FF7A00 0%, #FF5E00 100%); border-radius: 12px; padding: 20px; color: #FFFFFF !important; }
    .chevron-timeline { display: flex; align-items: center; background: transparent; padding: 10px 0; }
    .chevron-step { background: #E2E8F0; padding: 12px; flex-grow: 1; text-align: center; clip-path: polygon(0% 0%, 94% 0%, 100% 50%, 94% 100%, 0% 100%, 6% 50%); }
    .chevron-step.completed { background: #27AE60 !important; color: white; }
    .chevron-step.active { background: #0F2537 !important; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- UTILS DATABASE ---
def get_db_connection(): return sqlite3.connect("metalsuivi_saas.db", check_same_thread=False, timeout=10)
def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS licences (id INTEGER PRIMARY KEY AUTOINCREMENT, cle_licence TEXT UNIQUE, statut TEXT, date_expiration TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS entreprises (id INTEGER PRIMARY KEY AUTOINCREMENT, nom_entreprise TEXT, email TEXT UNIQUE, mot_de_passe TEXT, date_inscription TEXT, licence_active TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS projets (id INTEGER PRIMARY KEY AUTOINCREMENT, entreprise_id INTEGER, code_projet TEXT UNIQUE, nom_projet TEXT, client_nom TEXT, client_telephone TEXT, tonnage REAL, finition TEXT, date_creation TEXT, etape_actuelle TEXT, bat_status TEXT, bat_commentaire TEXT, liste_colisage TEXT)')
    conn.commit(); conn.close()

init_db()

# --- FONCTIONS LOGIQUES ---
def generer_nouvelle_licence(jours=30):
    conn = get_db_connection()
    c = conn.cursor()
    cle = f"LIC-{secrets.token_hex(2).upper()}"
    exp = (datetime.today() + timedelta(days=jours)).strftime('%Y-%m-%d')
    c.execute("INSERT INTO licences (cle_licence, statut, date_expiration) VALUES (?, 'disponible', ?)", (cle, exp))
    conn.commit(); conn.close()
    return cle

def verifier_et_activer_licence(cle):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT statut, date_expiration FROM licences WHERE cle_licence = ?", (cle,))
    res = c.fetchone()
    if res and res[0] == 'disponible':
        c.execute("UPDATE licences SET statut = 'utilisee' WHERE cle_licence = ?", (cle,))
        conn.commit(); conn.close(); return True
    conn.close(); return False

def requete_paiement_paytech(item_name, price):
    headers = {"Accept": "application/json", "Content-Type": "application/json", "API_KEY": PAYTECH_API_KEY, "API_SECRET": PAYTECH_SECRET_KEY}
    payload = {
        "item_name": item_name, "item_price": price, "currency": "XOF",
        "ref_command": f"CMD-{secrets.token_hex(4).upper()}", "env": "prod",
        "success_url": CALLBACK_URL + "?status=success", "cancel_url": CALLBACK_URL + "?status=cancel"
    }
    try:
        res = requests.post(PAYTECH_URL, json=payload, headers=headers).json()
        return res.get("redirect_url") if res.get("success") == 1 else None
    except: return None

# --- SESSIONS & UI ---
if "connected_at" not in st.session_state: st.session_state["connected_at"] = None

# GESTION RETOUR PAIEMENT
if st.query_params.get("status") == "success":
    st.balloons()
    st.success("🎉 Paiement validé ! Votre clé est générée.")
    st.code(generer_nouvelle_licence(30))
    st.query_params.clear()

with st.sidebar:
    menu = st.radio("Navigation", ["🏢 Espace Atelier (SaaS)", "🔐 Espace Suivi Client", "🛠️ Générateur Licences (Admin)"])

# --- PAGES ---
if menu == "🏢 Espace Atelier (SaaS)":
    if not st.session_state["connected_at"]:
        tab1, tab2, tab3 = st.tabs(["🔑 Connexion", "📝 Création", "🛒 Acheter une Licence"])
        with tab3:
            if st.button("Payer l'abonnement 10 000 F CFA"):
                url = requete_paiement_paytech("Abonnement MétalSuivi", 10000)
                if url: st.link_button("Finaliser le paiement", url)
    else:
        st.write(f"Connecté : {st.session_state['connected_at']}")

elif menu == "🛠️ Générateur Licences (Admin)":
    if st.button("Générer clé"): st.code(generer_nouvelle_licence())

elif menu == "🔐 Espace Suivi Client":
    st.title("Suivi")
