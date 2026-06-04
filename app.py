import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import secrets
import urllib.parse
import hashlib
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="MétalSuivi SaaS Enterprise", page_icon="🏗️", layout="wide")

# --- CONFIGURATION API PAYTECH ---
PAYTECH_API_KEY =st.secrets["b1eb4d11f8b411b35b53e69bcd5525ee6a76d726e8b9d835307f57b69cfd8489"] 
PAYTECH_SECRET_KEY = st.secrets["6a845d58ca0ba02b57829b4a3a4e9fa449bc8a7e7b7822d93f2bd8c7fb7fd94b"]
PAYTECH_URL = "https://paytech.sn/api/payment/request-payment" 

# --- DESIGN GRAPHIQUE GLOBAL INSPIRÉ DE LWS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F4F8FA !important;
        font-family: 'Poppins', sans-serif !important;
        color: #0F2537 !important;
    }
    
    /* --- BARRE LATÉRALE (SIDEBAR) --- */
    [data-testid="stSidebar"] {
        background-color: #1E2432 !important; 
        border-right: 1px solid #2D3748 !important;
    }
    [data-testid="stSidebar"] p {
        color: #94A3B8 !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.8rem !important;
        margin-bottom: 10px;
    }
    div[data-testid="stSidebarUserContent"] div[role="radiogroup"] [data-testid="stWidgetLabel"] {
        display: none !important; 
    }
    div[data-testid="stSidebarUserContent"] div[role="radiogroup"] label {
        background-color: #2A3245 !important;
        border: 1px solid #3B465E !important;
        padding: 14px 16px !important;
        border-radius: 8px !important;
        color: #CBD5E1 !important;
        font-weight: 500 !important;
        transition: all 0.25s ease-in-out !important;
        width: 100% !important;
        display: flex !important;
        margin-bottom: 8px !important;
    }
    div[data-testid="stSidebarUserContent"] div[role="radiogroup"] label[data-checked="true"] {
        background: linear-gradient(135deg, #FF5E00 0%, #D34E00 100%) !important; 
        border-color: #FF5E00 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(255, 94, 0, 0.2);
    }

    /* --- RECTANGLES ET CARTES EN ORANGE LWS --- */
    .lws-card {
        background: linear-gradient(135deg, #FF5E00 0%, #FF7A00 100%) !important;
        padding: 35px;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(255, 94, 0, 0.25);
        margin-bottom: 25px;
        color: #FFFFFF !important;
    }
    
    .lws-title {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        line-height: 1.2 !important;
        margin-bottom: 15px !important;
    }
    .lws-subtitle {
        font-size: 1.1rem !important;
        color: #FFFFFF !important;
        margin-bottom: 25px !important;
        opacity: 0.95;
    }

    /* Listes d'avantages */
    .hero-bullets { margin-bottom: 25px; }
    .bullet-item {
        font-size: 1.05rem;
        margin-bottom: 10px;
        color: #FFFFFF !important;
        display: flex;
        align-items: center;
    }
    .bullet-item span.check {
        color: #0F2537 !important;
        font-weight: bold;
        margin-right: 10px;
        font-size: 1.2rem;
    }
    .bullet-item strong {
        color: #0F2537 !important;
    }

    /* Alignement du bloc prix */
    .price-section { 
        display: flex; 
        align-items: center; 
        gap: 20px; 
        margin-bottom: 20px; 
        flex-wrap: wrap;
    }
    .old-price { 
        font-size: 1.4rem; 
        text-decoration: line-through; 
        color: #0F2537 !important; 
        opacity: 0.7; 
        font-weight: 600;
    }
    .current-price-box {
        display: flex;
        align-items: baseline;
    }
    .big-price { 
        font-size: 3.5rem; 
        font-weight: 700; 
        color: #FFFFFF !important; 
        line-height: 1; 
    }
    .discount-badge { 
        background-color: #0F2537 !important; 
        color: #FFFFFF !important; 
        padding: 6px 14px; 
        border-radius: 20px; 
        font-weight: 700; 
        font-size: 0.85rem; 
    }

    /* boutons style bleu nuit */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #0F2537 0%, #1E3A52 100%) !important;
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        padding: 12px 30px !important;
        border-radius: 30px !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(15, 37, 55, 0.3) !important;
        transition: all 0.2s ease !important;
        width: 100%;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #1E3A52 0%, #0F2537 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(15, 37, 55, 0.5) !important;
    }

    /* Grille de fiches techniques */
    .metal-card-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 25px; }
    .metal-card {
        background: linear-gradient(135deg, #FF7A00 0%, #FF5E00 100%);
        border: 1px solid #FF8F33; border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        color: #FFFFFF !important;
    }
    .metal-card h4 { margin: 0 0 5px 0 !important; color: #0F2537 !important; font-size: 1.4rem !important; }

    /* Timeline */
    .chevron-timeline { display: flex; align-items: center; background-color: transparent; padding: 10px 0; margin-bottom: 25px; }
    .chevron-step {
        position: relative; background: #E2E8F0; color: #64748B; padding: 12px 15px 12px 30px;
        font-size: 0.85rem; font-weight: 600; flex-grow: 1; text-align: center; margin-right: 4px;
        clip-path: polygon(0% 0%, 94% 0%, 100% 50%, 94% 100%, 0% 100%, 6% 50%);
    }
    .chevron-step.completed { background: #27AE60 !important; color: #FFFFFF !important; }
    .chevron-step.active { background: #0F2537 !important; color: #FFFFFF !important; }
    </style>
""", unsafe_allow_html=True)

# --- UTILS DATABASE ---
def get_db_connection():
    return sqlite3.connect("metalsuivi_saas.db", check_same_thread=False, timeout=10)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS licences (id INTEGER PRIMARY KEY AUTOINCREMENT, cle_licence TEXT UNIQUE NOT NULL, statut TEXT DEFAULT \'disponible\', date_expiration TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS entreprises (id INTEGER PRIMARY KEY AUTOINCREMENT, nom_entreprise TEXT NOT NULL, email TEXT UNIQUE NOT NULL, mot_de_passe TEXT NOT NULL, date_inscription TEXT, licence_active TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS projets (id INTEGER PRIMARY KEY AUTOINCREMENT, entreprise_id INTEGER NOT NULL, code_projet TEXT UNIQUE NOT NULL, nom_projet TEXT NOT NULL, client_nom TEXT NOT NULL, client_telephone TEXT, tonnage REAL, finition TEXT, date_creation TEXT, etape_actuelle TEXT, bat_status TEXT DEFAULT \'En attente de plan\', bat_commentaire TEXT, liste_colisage TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS fil_actualite (id INTEGER PRIMARY KEY AUTOINCREMENT, code_projet TEXT, date_evenement TEXT, etape TEXT, commentaire TEXT, photo_blob BLOB)')
    conn.commit()
    conn.close()

init_db()

ETAPES = ["1. Études & Plans", "2. Débit & Soudure (Atelier)", "3. Traitement (Peinture/Galva)", "4. Livraison & Colisage", "5. Montage sur site"]

def generer_nouvelle_licence(jours_validite=30): # Changé par défaut à 30 jours pour un mois
    conn = get_db_connection()
    c = conn.cursor()
    nouvelle_cle = f"LIC-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"
    date_exp = (datetime.today() + timedelta(days=jours_validite)).strftime('%Y-%m-%d')
    try:
        c.execute("INSERT INTO licences (cle_licence, statut, date_expiration) VALUES (?, 'disponible', ?)", (nouvelle_cle, date_exp))
        conn.commit()
        return nouvelle_cle
    except sqlite3.Error: return None
    finally: conn.close()

def verifier_et_activer_licence(cle):
    conn = get_db_connection()
    c = conn.cursor()
    date_actuelle = datetime.today().strftime('%Y-%m-%d')
    try:
        c.execute("SELECT statut, date_expiration FROM licences WHERE cle_licence = ?", (cle,))
        res = c.fetchone()
        if res and res[0] == 'disponible' and res[1] >= date_actuelle:
            c.execute("UPDATE licences SET statut = 'utilisee' WHERE cle_licence = ?", (cle,))
            conn.commit()
            return True
        return False
    finally: conn.close()

def inscrire_entreprise(nom, email, password, cle_licence):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO entreprises (nom_entreprise, email, mot_de_passe, date_inscription, licence_active) VALUES (?, ?, ?, ?, ?)",
                  (nom, email, hash_password(password), datetime.today().strftime('%Y-%m-%d'), cle_licence))
        conn.commit()
        return True
    except sqlite3.IntegrityError: return False
    finally: conn.close()

def connecter_entreprise(email, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, nom_entreprise FROM entreprises WHERE email = ? AND mot_de_passe = ?", (email, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def creer_projet_saas(ent_id, nom, client, tel, tonnage, finition, colisage):
    conn = get_db_connection()
    c = conn.cursor()
    code = f"MS-{secrets.token_hex(2).upper()}"
    c.execute('INSERT INTO projets (entreprise_id, code_projet, nom_projet, client_nom, client_telephone, tonnage, finition, etape_actuelle, date_creation, liste_colisage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
              (ent_id, code, nom, client, tel, tonnage, finition, ETAPES[0], datetime.today().strftime('%Y-%m-%d %H:%M'), colisage))
    conn.commit()
    conn.close()
    return code

def requete_paiement_paytech(item_name, price, success_url="https://zunongroguhe-bit-metalsuivi-saas-app-hc0xsr.streamlit.app/"):
    headers = {"Accept": "application/json", "Content-Type": "application/json", "API_KEY": PAYTECH_API_KEY, "API_SECRET": PAYTECH_SECRET_KEY}
    payload = {"item_name": item_name, "item_price": price, "currency": "XOF", "ref_command": f"CMD-{secrets.token_hex(4).upper()}", "command_name": "Abonnement MétalSuivi Premium", "env": "prod", "success_url": success_url, "cancel_url": success_url}
    try:
        response = requests.post(PAYTECH_URL, json=payload, headers=headers)
        res_json = response.json()
        if res_json.get("success") == 1: return res_json.get("redirect_url")
        return None
    except Exception: return None

# --- GESTION DES SESSIONS ---
if "connected_at" not in st.session_state: st.session_state["connected_at"] = None
if "entreprise_id" not in st.session_state: st.session_state["entreprise_id"] = None

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.write("Navigation Système")
    menu = st.radio(label="Menu Principal", options=["🏢 Espace Atelier (SaaS)", "🔐 Espace Suivi Client", "🛠️ Générateur Licences (Admin)"], index=0)
    if st.session_state["connected_at"]:
        st.divider()
        st.write(f"Utilisateur connecté :\n**{st.session_state['connected_at']}**")
        if st.button("Se déconnecter", type="secondary"):
            st.session_state["connected_at"] = None
            st.session_state["entreprise_id"] = None
            st.rerun()

# --- MODE INTERFACES SYSTEME ---

# INTERFACE 1 : GÉNÉRATEUR DE LICENCES (ADMIN)
if menu == "🛠️ Générateur Licences (Admin)":
    html_admin = """
    <div class="lws-card">
        <h1 class="lws-title">Panneau de Contrôle Directeur</h1>
        <p class="lws-subtitle">Générez des clés d'activation manuelles pour vos clients premium hors-ligne.</p>
    </div>
    """.replace("\n", "")
    st.markdown(html_admin, unsafe_allow_html=True)
    
    duree = st.number_input("Durée de validité de la licence (en jours)", min_value=1, value=30) # Mis à 30 jours par défaut
    if st.button("Créer une clé Premium Manuellement ➔"):
        nouvelle_cle = generer_nouvelle_licence(duree)
        if nouvelle_cle:
            st.success("✅ Nouvelle clé d'activation générée avec succès :")
            st.code(nouvelle_cle, language="text")

# INTERFACE 2 : ESPACE ATELIER (SAAS)
elif menu == "🏢 Espace Atelier (SaaS)":
    if not st.session_state["connected_at"]:
        
        # Capture de retour PayTech
        parametres_url = st.query_params
        if "status" in parametres_url and parametres_url["status"] == "success":
            st.balloons()
            st.success("🎉 Paiement en ligne validé avec succès via PayTech !")
            cle_paytech_auto = generer_nouvelle_licence(30) # Génère pour 30 jours
            st.markdown("### 🔑 Votre Clé de Licence unique :\nCopiez-la et utilisez-la dans l'onglet **'Créer un compte'**.")
            st.code(cle_paytech_auto, language="text")
            st.query_params.clear()
            st.divider()

        tab_auth1, tab_auth2, tab_auth3 = st.tabs(["🔑 Se connecter", "📝 Créer un compte", "🛒 Acheter une Licence"])
        
        with tab_auth1:
            html_login = """
            <div class="lws-card">
                <h1 class="lws-title">Accès à votre Espace Atelier</h1>
                <p class="lws-subtitle">Connectez-vous pour piloter vos ouvrages, éditer vos B.A.T et suivre la production.</p>
            </div>
            """.replace("\n", "")
            st.markdown(html_login, unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("Adresse Email Professionnelle").strip()
                password = st.text_input("Mot de passe secret", type="password")
                if st.form_submit_button("Entrer dans mon espace atelier ➔"):
                    user = connecter_entreprise(email, password)
                    if user:
                        st.session_state["entreprise_id"] = user[0]
                        st.session_state["connected_at"] = user[1]
                        st.rerun()
                    else: st.error("Identifiants incorrects. Veuillez réessayer.")
                        
        with tab_auth2:
            html_register = """
            <div class="lws-card">
                <h1 class="lws-title">Activer votre Espace Dédié</h1>
                <p class="lws-subtitle">Remplissez le formulaire ci-dessous muni de votre clé LIC-XXXX pour ouvrir votre accès SaaS.</p>
            </div>
            """.replace("\n", "")
            st.markdown(html_register, unsafe_allow_html=True)
            with st.form("register_form"):
                new_nom = st.text_input("Nom de l'Atelier / Entreprise", placeholder="ex: Ivoire Structures SAS")
                new_email = st.text_input("Email de gestion principal")
                new_pass = st.text_input("Définir un mot de passe", type="password")
                cle_saisie = st.text_input("Clé d'activation Licence (LIC-XXXX-XXXX)").strip().upper()
                if st.form_submit_button("Valider et Activer mon Compte ➔"):
                    if new_nom and new_email and new_pass and cle_saisie:
                        if verifier_et_activer_licence(cle_saisie):
                            if inscrire_entreprise(new_nom, new_email, new_pass, cle_saisie): 
                                st.success("✅ Votre compte a été configuré ! Connectez-vous depuis le premier onglet.")
                            else: st.error("Cette adresse email est déjà enregistrée.")
                        else: st.error("❌ Cette clé de licence est invalide ou déjà consommée.")
                    else: st.error("Veuillez remplir l'intégralité des champs demandés.")

        with tab_auth3:
            if "paytech_clique" not in st.session_state:
                st.session_state["paytech_clique"] = False
            if "lien_paiement" not in st.session_state:
                st.session_state["lien_paiement"] = None

            zone_offre = st.container()

            if not st.session_state["paytech_clique"]:
                with zone_offre:
                    html_offre = """
                    <div class="lws-card">
                        <div style="text-transform: uppercase; letter-spacing: 1px; font-weight: 700; font-size: 0.85rem; margin-bottom: 10px; color: #0F2537;">
                            🔥 ABONNEMENT MENSUEL SANS ENGAGEMENT
                        </div>
                        <h1 class="lws-title">Créez votre suivi de chantier professionnel en 15 minutes</h1>
                        <div class="hero-bullets">
                            <div class="bullet-item"><span class="check">✓</span> <span><strong>Portail client</strong> personnalisé en sous-domaine offert</span></div>
                            <div class="bullet-item"><span class="check">✓</span> <span>Générateur de <strong>B.A.T numérique</strong> avec signature intégrée</span></div>
                            <div class="bullet-item"><span class="check">✓</span> <span><strong>Notifications WhatsApp</strong> automatisées basées sur l'avancement</span></div>
                        </div>
                        <div class="price-section">
                            <div class="old-price">25 000 F</div>
                            <div class="current-price-box">
                                <div class="big-price">10 000</div>
                                <div style="font-size: 1.1rem; color: #FFFFFF; margin-left: 5px; font-weight: 600; align-self: flex-end; margin-bottom: 8px;">F CFA / mois</div>
                            </div>
                            <div class="discount-badge">PRIX DE LANCEMENT</div>
                        </div>
                    </div>
                    """.replace("\n", "")
                    st.markdown(html_offre, unsafe_allow_html=True)
                    
                    if st.button("Activer mon abonnement mensuel ➔", key="btn_paytech_premium"):
                        with st.spinner("Génération de la passerelle sécurisée PayTech..."):
                            # Envoi du prix corrigé à 10000 F CFA
                            url_paiement = requete_paiement_paytech("Abonnement Mensuel MetalSuivi Pro", 10000)
                            if url_paiement:
                                st.session_state["lien_paiement"] = url_paiement
                                st.session_state["paytech_clique"] = True
                                st.rerun()
                            else:
                                st.error("Liaison API momentanément indisponible. Utilisez la simulation locale ci-dessous.")
            else:
                with zone_offre:
                    html_tunnel = """
                    <div class="lws-card" style="background: linear-gradient(135deg, #0F2537 0%, #1E3A52 100%) !important;">
                        <h3 style="color: #FFFFFF !important; margin-bottom: 15px;">🔒 Passerelle de Paiement Générée</h3>
                        <p style="color: #CBD5E1 !important;">Votre commande de 10 000 F CFA est prête. Cliquez sur le bouton sécurisé ci-dessous pour finaliser la transaction sur PayTech (Wave, Orange Money, Moov, MTN).</p>
                    </div>
                    """.replace("\n", "")
                    st.markdown(html_tunnel, unsafe_allow_html=True)
                    
                    st.link_button("👉 ACCÉDER AU PAIEMENT SÉCURISÉ", st.session_state["lien_paiement"], use_container_width=True)
                    
                    if st.button("⬅️ Retourner à l'offre", type="secondary"):
                        st.session_state["paytech_clique"] = False
                        st.session_state["lien_paiement"] = None
                        st.rerun()
            
            st.markdown("<br><hr style='border-color: #CBD5E1;'>", unsafe_allow_html=True)
            st.write("🔬 **Zone de Simulation (Test Local) :**")
            if st.button("Simuler un succès de paiement (Obtenir une clé immédiate)", type="secondary", key="btn_sim_premium"):
                cle_auto = generer_nouvelle_licence(30) # Donne 30 jours d'accès
                st.success("🎉 Paiement simulé avec succès !")
                st.code(cle_auto, language="text")

    else:
        # ESPACE ATELIER CONNECTÉ
        html_connected = f'<div class="lws-card" style="padding:20px;"><h3 style="margin:0; color:white;">🏗️ Connecté au Bureau d\'Études : {st.session_state["connected_at"]}</h3></div>'.replace("\n", "")
        st.markdown(html_connected, unsafe_allow_html=True)
        
        t1, t2, t3 = st.tabs(["📋 Nos Chantiers Actifs", "➕ Enregistrer un Ouvrage", "⚙️ Publier une Avancée"])
        current_id = st.session_state["entreprise_id"]
        
        with t2:
            html_new_dossier = """
            <div class="lws-card">
                <h2 class="lws-title">Lancer un nouveau dossier de fabrication</h2>
                <p class="lws-subtitle">Enregistrez l'ouvrage pour générer immédiatement les accès uniques de suivi de votre client.</p>
            </div>
            """.replace("\n", "")
            st.markdown(html_new_dossier, unsafe_allow_html=True)
            with st.form("form_new_saas"):
                c1, c2 = st.columns(2)
                with c1:
                    nom = st.text_input("Nom de l'ouvrage / Projet", placeholder="ex: Hangar de Stockage")
                    client = st.text_input("Nom du Client / Raison sociale")
                    tel = st.text_input("N° WhatsApp du Client")
                with c2:
                    tonnage = st.number_input("Tonnage Acier estimé (en Tonnes)", min_value=0.1, value=10.0)
                    finition = st.selectbox("Type de Finition de surface", ["Peinture Antirouille", "Galvanisation", "Brut"])
                    colisage = st.text_area("Éléments de Colisage Initiaux", "Poteaux\nPoutres\nAccessoires")
                if st.form_submit_button("Créer le Dossier d'Ouvrage ➔") and nom and client:
                    code_g = creer_projet_saas(current_id, nom, client, tel, tonnage, finition, colisage)
                    st.success(f"🚀 Projet ajouté ! CODE CLIENT UNIQUE : {code_g}")

        with t1:
            html_chantiers = """
            <div class="lws-card">
                <h2 class="lws-title">Chantiers en cours de traitement</h2>
                <p class="lws-subtitle">Vue d'ensemble en temps réel de l'état d'avancement de vos structures métalliques.</p>
            </div>
            """.replace("\n", "")
            st.markdown(html_chantiers, unsafe_allow_html=True)
            conn = get_db_connection()
            df = pd.read_sql_query(f"SELECT code_projet AS 'Code Unique', nom_projet AS 'Ouvrage', client_nom AS 'Client', etape_actuelle AS 'Étape Actuelle', bat_status AS 'Statut B.A.T' FROM projets WHERE entreprise_id = {current_id}", conn)
            conn.close()
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else: st.info("Aucun chantier actif pour le moment.")

        with t3:
            html_avancement = """
            <div class="lws-card">
                <h2 class="lws-title">Faire progresser le statut de fabrication</h2>
                <p class="lws-subtitle">Mettez à jour les étapes pour notifier instantanément le client sur son portail web.</p>
            </div>
            """.replace("\n", "")
            st.markdown(html_avancement, unsafe_allow_html=True)
            conn = get_db_connection()
            projets_dispos = pd.read_sql_query(f"SELECT code_projet, nom_projet FROM projets WHERE entreprise_id = {current_id}", conn)
            conn.close()
            
            if not projets_dispos.empty:
                liste_p = {f"{row['code_projet']} - {row['nom_projet']}": row['code_projet'] for _, row in projets_dispos.iterrows()}
                p_sel = st.selectbox("Sélectionner l'ouvrage concerné", list(liste_p.keys()))
                code_projet_sel = liste_p[p_sel]
                
                et = st.selectbox("Définir la nouvelle étape majeure", ETAPES)
                comm = st.text_area("Note d'atelier interne / Observations")
                if st.button("Mettre à jour l'avancement général ➔"):
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("UPDATE projets SET etape_actuelle = ? WHERE code_projet = ? AND entreprise_id = ?", (et, code_projet_sel, current_id))
                    c.execute("INSERT INTO fil_actualite (code_projet, date_evenement, etape, commentaire, photo_blob) VALUES (?,?,?,?,?)",
                              (code_projet_sel, datetime.today().strftime('%Y-%m-%d %H:%M'), et, comm, None))
                    conn.commit()
                    conn.close()
                    st.success("✅ Statut mis à jour et synchronisé avec le client !")

# INTERFACE 3 : PORTAIL CLIENT (SUIVI DE CHANTIER)
elif menu == "🔐 Espace Suivi Client":
    html_suivi = """
    <div class="lws-card">
        <h1 class="lws-title">Suivi de Fabrication en Temps Réel</h1>
        <p class="lws-subtitle">Entrez le code de suivi unique fourni par votre atelier de charpente pour suivre l'évolution.</p>
    </div>
    """.replace("\n", "")
    st.markdown(html_suivi, unsafe_allow_html=True)
    
    code_saisi = st.text_input("Code de suivi unique (ex: MS-XXXX) :", placeholder="MS-XXXX").strip().upper()
    if code_saisi:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT p.nom_projet, p.client_nom, p.tonnage, p.finition, p.etape_actuelle, p.bat_status, p.bat_commentaire, p.liste_colisage, e.nom_entreprise FROM projets p JOIN entreprises e ON p.entreprise_id = e.id WHERE p.code_projet = ?', (code_saisi,))
        p = c.fetchone()
        if p:
            nom, client, tonnage, finition, etape, bat_status, bat_comm, colisage, nom_entreprise = p
            
            st.markdown(f'<div style="background-color: #0F2537; color: white; padding: 12px 16px; border-radius: 8px; font-weight: 500; margin-bottom: 25px;">🔓 Suivi de structure actif • Constructeur attitré : <b>{nom_entreprise}</b></div>', unsafe_allow_html=True)
            
            html_grid = f"""
            <div class="metal-card-grid">
                <div class="metal-card"><h4 style="color: white !important;">{nom}</h4>Nom de l'ouvrage</div>
                <div class="metal-card"><h4 style="color: white !important;">{tonnage} T</h4>Masse globale acier</div>
                <div class="metal-card"><h4 style="color: white !important;">{finition}</h4>Traitement de surface</div>
            </div>
            """.replace("\n", "")
            st.markdown(html_grid, unsafe_allow_html=True)
            
            st.write("📊 **Progression linéaire de l'usinage :**")
            etape_index = 0
            for i, et_text in enumerate(ETAPES):
                if et_text in etape: etape_index = i
            
            timeline_html = '<div class="chevron-timeline">'
            for i, et_text in enumerate(ETAPES):
                status_class = "chevron-step"
                if i < etape_index: status_class = "chevron-step completed"
                elif i == etape_index: status_class = "chevron-step active"
                timeline_html += f'<div class="{status_class}">{et_text}</div>'
            timeline_html += '</div>'
            st.markdown(timeline_html.replace("\n", ""), unsafe_allow_html=True)
            
            st.info(f"📦 **Colisage d'expédition enregistré à l'atelier :**\n\n{colisage}")
            
        else: st.error("❌ Code introuvable.")
        conn.close()
