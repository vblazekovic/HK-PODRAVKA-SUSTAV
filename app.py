
# app.py — HK Podravka Admin (Sekcija 1)
# Pokreni: streamlit run app.py

import os
import json
from io import BytesIO
from datetime import datetime
import streamlit as st

# -------------------------------------------------
# Page config mora biti na vrhu
# -------------------------------------------------
st.set_page_config(page_title="HK Podravka — Admin", page_icon="🥇", layout="wide")

# -------------------------------------------------
# Brand & CSS (bez f-string evaluacije u CSS-u)
# -------------------------------------------------
BRAND = {"red": "#C81414", "gold": "#C8A94A", "white": "#FFFFFF"}

def _inject_brand_css():
    css = """
    <style>
        :root {
            --brand-red: __RED__;
            --brand-gold: __GOLD__;
            --brand-white: __WHITE__;
        }
        .brand-card {
            border: 1px solid rgba(0,0,0,0.08);
            border-radius: 14px;
            padding: 14px 18px;
            background: var(--brand-white);
            box-shadow: 0 2px 16px rgba(0,0,0,0.04);
        }
        .brand-badge {
            background: var(--brand-gold);
            color: #111;
            font-weight: 700;
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 12px;
            letter-spacing: .3px;
        }
        .brand-title { font-weight: 800; font-size: 22px; margin: 0; }
        .brand-sub { color:#555; font-size: 13px; margin-top:2px; }
        .brand-hr { border: none; height: 1px; background: rgba(0,0,0,.08); margin: 10px 0 12px 0; }
        .required:after { content:" *"; color: var(--brand-red); font-weight: 900; }
        .stDownloadButton button, .stButton>button { border-radius: 10px !important; font-weight: 700 !important; }
        .muted { color:#666; font-size:12px; }
        .danger { color:#B00020; font-weight:700; }
        .ok { color:#0B7C2B; font-weight:700; }
    </style>
    """.replace("__RED__", BRAND["red"]).replace("__GOLD__", BRAND["gold"]).replace("__WHITE__", BRAND["white"])
    st.markdown(css, unsafe_allow_html=True)

# -------------------------------------------------
# State init
# -------------------------------------------------
def _init_state():
    ss = st.session_state
    if "club_data" not in ss:
        ss.club_data = {
            "klub": "HRVAČKI KLUB PODRAVKA",
            "ulica": "Miklinovec 6a",
            "grad_postanski": "48000 Koprivnica",
            "iban": "HR6923860021100518154",
            "oib": "60911784858",
            "email": "hsk-podravka@gmail.com",
            "web": "https://hk-podravka.com",
            "social": {"instagram": "", "facebook": "", "tiktok": ""},
            "predsjednik": {"ime_prezime": "", "kontakt": "", "email": ""},
            "tajnik": {"ime_prezime": "", "kontakt": "", "email": ""},
            "predsjednistvo": [],
            "nadzorni_odbor": [],
            "dokumenti": {"statut": None, "ostali": []},
            "logo_path_hint": "assets/logo.png",
        }

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _download_json_button(data, label, filename):
    buf = BytesIO()
    buf.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
    st.download_button(label=label, data=buf.getvalue(), file_name=filename, mime="application/json")

def _upload_json_and_load(label, key):
    up = st.file_uploader(label, type=["json"], key=key)
    if up is not None:
        try:
            loaded = json.load(up)
            st.session_state.club_data = loaded
            st.success("✅ Učitani podaci su uspješno postavljeni.")
        except Exception as e:
            st.error(f"⚠️ Greška pri učitavanju JSON-a: {e}")

def _safe_logo_image(path: str, sidebar=False):
    exists = os.path.exists(path)
    html_badge = """
    <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:44px;height:44px;border-radius:50%;background:#C81414;
                    display:flex;align-items:center;justify-content:center;color:#fff;font-weight:900;">
            HK
        </div>
        <div style="font-weight:800;">HK PODRAVKA</div>
    </div>
    """
    if sidebar:
        if exists:
            st.sidebar.image(path, use_column_width=True)
        else:
            st.sidebar.markdown(html_badge, unsafe_allow_html=True)
    else:
        if exists:
            st.image(path, use_column_width=True)
        else:
            st.markdown(html_badge, unsafe_allow_html=True)

def _people_simple_editor(title: str, list_key: str, help_text: str = ""):
    """Editor kompatibilan s ranijim verzijama Streamlita (bez data_editor)."""
    st.markdown(f"### {title}")
    if help_text:
        st.caption(help_text)

    data = st.session_state.club_data.get(list_key, [])
    if not isinstance(data, list):
        data = []
    # Prikaz postojeće liste
    if data:
        for idx, person in enumerate(data):
            with st.expander(f"{idx+1}. {person.get('ime_prezime','(bez imena)')}", expanded=False):
                pcol1, pcol2 = st.columns([1,1])
                with pcol1:
                    st.text_input("Ime i prezime", key=f"{list_key}_{idx}_ime", value=person.get("ime_prezime",""))
                    st.text_input("Kontakt broj", key=f"{list_key}_{idx}_kontakt", value=person.get("kontakt",""))
                with pcol2:
                    st.text_input("E-mail adresa", key=f"{list_key}_{idx}_email", value=person.get("email",""))
                    if st.button("🗑️ Obriši", key=f"{list_key}_{idx}_del"):
                        data.pop(idx)
                        st.session_state.club_data[list_key] = data
                        st.experimental_rerun()
        st.markdown("---")
    else:
        st.caption("Nema upisanih osoba.")

    # Dodavanje nove osobe
    st.markdown("**Dodaj osobu**")
    ac1, ac2, ac3 = st.columns([1,1,1])
    with ac1:
        _new_ime = st.text_input("Ime i prezime (novo)", key=f"add_{list_key}_ime", value="")
    with ac2:
        _new_kontakt = st.text_input("Kontakt broj (novo)", key=f"add_{list_key}_kontakt", value="")
    with ac3:
        _new_email = st.text_input("E-mail (novo)", key=f"add_{list_key}_email", value="")
    if st.button("➕ Dodaj", key=f"add_{list_key}_btn"):
        record = {"ime_prezime": _new_ime.strip(), "kontakt": _new_kontakt.strip(), "email": _new_email.strip()}
        data.append(record)
        st.session_state.club_data[list_key] = data
        st.success("Dodano.")
        st.experimental_rerun()

# -------------------------------------------------
# Sekcija 1 — Osnovni podaci
# -------------------------------------------------
def render_prvi_odjeljak():
    _inject_brand_css()
    _init_state()

    # Header
    with st.container():
        cols = st.columns([1, 3])
        with cols[0]:
            st.markdown('<div class="brand-badge">HK PODRAVKA</div>', unsafe_allow_html=True)
            logo_col1, logo_col2 = st.columns([1,1])
            with logo_col1:
                _safe_logo_image(st.session_state.club_data.get("logo_path_hint", "assets/logo.png"))
                st.caption("Logo (putanja)")
            with logo_col2:
                new_logo = st.file_uploader("Promijeni logo (PNG/JPG)", type=["png","jpg","jpeg"], key="logo_upload")
                if new_logo:
                    st.image(new_logo, caption="Novi logo (nespremjeno u datoteke)", use_column_width=True)
                    st.info("Napomena: U ovoj fazi logo se ne sprema na disk. Path možeš promijeniti dolje u polju 'Putanja do loga'.")
        with cols[1]:
            st.markdown('<p class="brand-title">Administracija — Osnovni podaci o klubu</p>', unsafe_allow_html=True)
            st.markdown('<p class="brand-sub">Centralno mjesto za unos i uređivanje službenih podataka kluba. Dizajn je prilagođen za mobitele.</p>', unsafe_allow_html=True)

    st.markdown('<hr class="brand-hr" />', unsafe_allow_html=True)

    # Osnovni podaci
    with st.container():
        st.markdown("### 🏛️ Osnovni podaci")
        bcol1, bcol2, bcol3 = st.columns([1.1,1,1])
        with bcol1:
            st.text_input("KLUB (IME)", key="cd_klub", value=st.session_state.club_data["klub"])
            st.text_input("ULICA I KUĆNI BROJ", key="cd_ulica", value=st.session_state.club_data["ulica"])
            st.text_input("GRAD I POŠTANSKI BROJ", key="cd_grad", value=st.session_state.club_data["grad_postanski"])
        with bcol2:
            st.text_input("IBAN RAČUN", key="cd_iban", value=st.session_state.club_data["iban"])
            st.text_input("OIB", key="cd_oib", value=st.session_state.club_data["oib"])
            st.text_input("E-mail", key="cd_email", value=st.session_state.club_data["email"])
        with bcol3:
            st.text_input("Web stranica", key="cd_web", value=st.session_state.club_data["web"])
            st.text_input("Putanja do loga", key="cd_logo_path", value=st.session_state.club_data.get("logo_path_hint","assets/logo.png"))
            st.markdown("&nbsp;")

    # Društvene mreže
    st.markdown("### 🔗 Društvene mreže")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.text_input("Instagram URL", key="cd_instagram", value=st.session_state.club_data["social"].get("instagram",""))
    with s2:
        st.text_input("Facebook URL", key="cd_facebook", value=st.session_state.club_data["social"].get("facebook",""))
    with s3:
        st.text_input("TikTok URL", key="cd_tiktok", value=st.session_state.club_data["social"].get("tiktok",""))

    st.markdown('<hr class="brand-hr" />', unsafe_allow_html=True)

    # Tijela kluba
    st.markdown("### 👥 Tijela kluba")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Predsjednik**")
        p_ime = st.text_input("Ime i prezime (predsjednik)", key="cd_preds_ime", value=st.session_state.club_data["predsjednik"]["ime_prezime"])
        p_kontakt = st.text_input("Kontakt broj (predsjednik)", key="cd_preds_kontakt", value=st.session_state.club_data["predsjednik"]["kontakt"])
        p_email = st.text_input("E-mail (predsjednik)", key="cd_preds_email", value=st.session_state.club_data["predsjednik"]["email"])
    with c2:
        st.markdown("**Tajnik**")
        t_ime = st.text_input("Ime i prezime (tajnik)", key="cd_taj_ime", value=st.session_state.club_data["tajnik"]["ime_prezime"])
        t_kontakt = st.text_input("Kontakt broj (tajnik)", key="cd_taj_kontakt", value=st.session_state.club_data["tajnik"]["kontakt"])
        t_email = st.text_input("E-mail (tajnik)", key="cd_taj_email", value=st.session_state.club_data["tajnik"]["email"])

    # Simple editori (kompatibilno)
    _people_simple_editor("Članovi predsjedništva", "predsjednistvo", help_text="Dodajte/uređujte članove. Koristite 'Dodaj' za novi red, a u svakom redu 'Obriši'.")
    _people_simple_editor("Nadzorni odbor", "nadzorni_odbor", help_text="Dodajte/uređujte članove. Koristite 'Dodaj' za novi red, a u svakom redu 'Obriši'.")

    st.markdown('<hr class="brand-hr" />', unsafe_allow_html=True)

    # Dokumenti
    st.markdown("### 📄 Dokumenti")
    dcol1, dcol2 = st.columns([1,1])
    with dcol1:
        statut_file = st.file_uploader("Upload — Statut kluba (PDF/Doc)", type=["pdf","doc","docx"])
        if statut_file:
            st.session_state.club_data["dokumenti"]["statut"] = {
                "name": statut_file.name,
                "uploaded_at": datetime.now().isoformat(timespec="seconds")
            }
            st.success(f"Statut učitan: {statut_file.name}")
        current_statut = st.session_state.club_data["dokumenti"]["statut"]
        if current_statut:
            st.info(f"Trenutno postavljen Statut: **{current_statut['name']}** (upload: {current_statut['uploaded_at']})")
    with dcol2:
        other_files = st.file_uploader("Upload — Ostali dokumenti (više datoteka)", accept_multiple_files=True, type=["pdf","jpg","jpeg","png","doc","docx","xls","xlsx"])
        if other_files:
            for f in other_files:
                st.session_state.club_data["dokumenti"]["ostali"].append({
                    "name": f.name,
                    "uploaded_at": datetime.now().isoformat(timespec="seconds")
                })
            st.success(f"Učitano: {len(other_files)} dokumenata")
        if st.session_state.club_data["dokumenti"]["ostali"]:
            st.write("**Popis ostalih dokumenata:**")
            st.dataframe(st.session_state.club_data["dokumenti"]["ostali"], use_container_width=True)

    st.markdown('<hr class="brand-hr" />', unsafe_allow_html=True)

    # Spremanje/Uvoz
    st.markdown("### 💾 Spremanje / Uvoz podataka")
    with st.container():
        st.session_state.club_data.update({
            "klub": st.session_state.cd_klub,
            "ulica": st.session_state.cd_ulica,
            "grad_postanski": st.session_state.cd_grad,
            "iban": st.session_state.cd_iban,
            "oib": st.session_state.cd_oib,
            "email": st.session_state.cd_email,
            "web": st.session_state.cd_web,
            "logo_path_hint": st.session_state.cd_logo_path,
            "social": {
                "instagram": st.session_state.cd_instagram,
                "facebook": st.session_state.cd_facebook,
                "tiktok": st.session_state.cd_tiktok,
            },
            "predsjednik": {"ime_prezime": p_ime, "kontakt": p_kontakt, "email": p_email},
            "tajnik": {"ime_prezime": t_ime, "kontakt": t_kontakt, "email": t_email},
        })

        sc1, sc2, sc3 = st.columns([1,1,1])
        with sc1:
            _download_json_button(st.session_state.club_data, "⬇️ Preuzmi JSON (sekcija 1)", "hk_podravka_osnovni_podaci.json")
        with sc2:
            _upload_json_and_load("⬆️ Uvezi JSON (sekcija 1)", key="json_upload_1")
        with sc3:
            if st.button("✅ Spremi u session (lokalno)"):
                st.success("Podaci su ažurirani u memoriji aplikacije.")

    st.markdown('<hr class="brand-hr" />', unsafe_allow_html=True)
    st.caption("© HK Podravka — Admin modul · Boje: crvena, bijela, zlatna · Sekcija 1/8")

# -------------------------------------------------
# Bootstrap — Sidebar i navigacija
# -------------------------------------------------
_inject_brand_css()
_init_state()
_safe_logo_image("assets/logo.png", sidebar=True)
st.sidebar.markdown("### HK Podravka — Admin")

section = st.sidebar.radio(
    "Odaberite odjeljak",
    [
        "1) Osnovni podaci",
        "2) Članovi (soon)",
        "3) Treneri (soon)",
        "4) Natjecanja i rezultati (soon)",
        "5) Statistika (soon)",
        "6) Grupe (soon)",
        "7) Veterani (soon)",
        "8) Prisustvo (soon)",
        "9) Komunikacije (soon)",
        "10) Članarine (soon)",
    ],
    index=0
)

if section.startswith("1"):
    render_prvi_odjeljak()
else:
    st.info("Ovaj odjeljak će biti dodan u sljedećim koracima. Trenutno je aktivna Sekcija 1 — Osnovni podaci o klubu.")

