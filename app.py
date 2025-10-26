
# app.py — HK Podravka Admin (Sekcija 1 + Sekcija 2)

import os
import json
from io import BytesIO
from datetime import datetime, date
import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="HK Podravka — Admin", page_icon="🥇", layout="wide")

BRAND = {"red": "#C81414", "gold": "#C8A94A", "white": "#FFFFFF"}

def _inject_brand_css():
    css = """
    <style>
        :root {
            --brand-red: __RED__;
            --brand-gold: __GOLD__;
            --brand-white: __WHITE__;
        }
        .brand-hr { border: none; height: 1px; background: rgba(0,0,0,.08); margin: 10px 0 12px 0; }
        .danger { color:#B00020; font-weight:700; }
        .ok { color:#0B7C2B; font-weight:700; }
    </style>
    """.replace("__RED__", BRAND["red"]).replace("__GOLD__", BRAND["gold"]).replace("__WHITE__", BRAND["white"])
    st.markdown(css, unsafe_allow_html=True)

# -------------------------------------------------
# GLOBAL STATE INIT
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
    if "members" not in ss:
        ss.members = []
    if "groups" not in ss:
        ss.groups = ["Početnici", "U11", "U13", "U15", "U17", "U20", "Seniori", "Veterani"]

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

# -------------------------------------------------
# SEKCIJA 1 — OSNOVNI PODACI
# -------------------------------------------------
def render_prvi_odjeljak():
    _inject_brand_css()
    _init_state()

    st.markdown("## 🏛️ Osnovni podaci o klubu")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Naziv kluba", key="cd_klub", value=st.session_state.club_data["klub"])
        st.text_input("Ulica i broj", key="cd_ulica", value=st.session_state.club_data["ulica"])
        st.text_input("Grad i poštanski broj", key="cd_grad", value=st.session_state.club_data["grad_postanski"])
    with c2:
        st.text_input("IBAN", key="cd_iban", value=st.session_state.club_data["iban"])
        st.text_input("OIB", key="cd_oib", value=st.session_state.club_data["oib"])
        st.text_input("E-mail", key="cd_email", value=st.session_state.club_data["email"])
    with c3:
        st.text_input("Web stranica", key="cd_web", value=st.session_state.club_data["web"])
        st.text_input("Putanja do loga", key="cd_logo_path", value=st.session_state.club_data["logo_path_hint"])
        _safe_logo_image(st.session_state.club_data.get("logo_path_hint", "assets/logo.png"))

    st.markdown("<hr class='brand-hr'/>", unsafe_allow_html=True)
    st.markdown("### 🔗 Društvene mreže")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.text_input("Instagram", key="cd_instagram", value=st.session_state.club_data["social"].get("instagram", ""))
    with s2:
        st.text_input("Facebook", key="cd_facebook", value=st.session_state.club_data["social"].get("facebook", ""))
    with s3:
        st.text_input("TikTok", key="cd_tiktok", value=st.session_state.club_data["social"].get("tiktok", ""))

# -------------------------------------------------
# SEKCIJA 2 — ČLANOVI
# -------------------------------------------------
def _pdf_template(title, member, text):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"<b>{title}</b>", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Ime i prezime: <b>{member.get('ime','')}</b>", styles["Normal"]),
        Paragraph(f"Datum rođenja: <b>{member.get('datum_rodenja','')}</b>", styles["Normal"]),
        Paragraph(f"OIB: <b>{member.get('oib','')}</b>", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(text, styles["Normal"]),
    ]
    doc.build(story)
    buf.seek(0)
    return buf

def render_clanovi_section():
    _init_state()
    st.markdown("## 👤 Članovi kluba")

    ime = st.text_input("Ime i prezime")
    datum = st.date_input("Datum rođenja", value=date(2010, 1, 1))
    spol = st.selectbox("Spol", ["", "M", "Ž"])
    oib = st.text_input("OIB")
    mjesto = st.text_input("Mjesto prebivališta")
    aktivni = st.checkbox("Aktivni natjecatelj/ica")
    veteran = st.checkbox("Veteran")
    placa = st.checkbox("Plaća članarinu", value=True)
    iznos = st.number_input("Iznos članarine (€)", value=30.0, step=5.0)
    grupa = st.selectbox("Grupa", [""] + st.session_state.groups)
    nova_grupa = st.text_input("Dodaj novu grupu")
    if st.button("➕ Dodaj grupu"):
        g = nova_grupa.strip()
        if g and g not in st.session_state.groups:
            st.session_state.groups.append(g)
            st.success(f"Dodana grupa: {g}")

    foto = st.file_uploader("Fotografija (opcionalno)", type=["jpg","jpeg","png"])
    lpotvrda = st.file_uploader("Liječnička potvrda (PDF/JPG)", type=["pdf","jpg","jpeg"])
    vrijedi_do = st.text_input("Potvrda vrijedi do (YYYY-MM-DD)")
    napomena = st.text_area("Napomena")

    if st.button("💾 Spremi člana"):
        member = {
            "ime": ime,
            "datum_rodenja": str(datum),
            "spol": spol,
            "oib": oib,
            "mjesto": mjesto,
            "aktivni": aktivni,
            "veteran": veteran,
            "placa": placa,
            "iznos": iznos if placa else 0,
            "grupa": grupa,
            "napomena": napomena,
            "vrijedi_do": vrijedi_do,
            "fotografija": foto.name if foto else "",
        }
        st.session_state.members.append(member)
        st.success(f"Član {ime} dodan.")

        pristupnica_text = "Pristupnica HK Podravka — tekst prema Statutu i pravilima kluba."
        privola_text = "Privola za obradu osobnih podataka sukladno GDPR uredbi."
        prist_pdf = _pdf_template("PRISTUPNICA — HK PODRAVKA", member, pristupnica_text)
        priv_pdf = _pdf_template("PRIVOLA — HK PODRAVKA", member, privola_text)
        st.download_button("⬇️ Preuzmi PRISTUPNICU (PDF)", prist_pdf, file_name=f"pristupnica_{oib}.pdf", mime="application/pdf")
        st.download_button("⬇️ Preuzmi PRIVOLU (PDF)", priv_pdf, file_name=f"privola_{oib}.pdf", mime="application/pdf")

    st.markdown("<hr class='brand-hr'/>", unsafe_allow_html=True)
    st.markdown("### 📋 Popis članova")

    if not st.session_state.members:
        st.info("Još nema unesenih članova.")
    else:
        for i, m in enumerate(st.session_state.members):
            with st.expander(f"{i+1}. {m['ime']}"):
                st.write(f"Datum rođenja: {m['datum_rodenja']}")
                st.write(f"OIB: {m['oib']}")
                st.write(f"Spol: {m['spol']}")
                st.write(f"Grupa: {m['grupa']}")
                st.write(f"Iznos članarine: {m['iznos']} €")
                st.write(f"Aktivni: {'DA' if m['aktivni'] else 'NE'}")
                st.write(f"Veteran: {'DA' if m['veteran'] else 'NE'}")
                st.write(f"Napomena: {m['napomena']}")

# -------------------------------------------------
# SIDEBAR NAVIGACIJA
# -------------------------------------------------
_inject_brand_css()
_init_state()
_safe_logo_image("assets/logo.png", sidebar=True)
st.sidebar.markdown("### HK Podravka — Admin")

section = st.sidebar.radio(
    "Odaberite odjeljak",
    [
        "1) Osnovni podaci",
        "2) Članovi",
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
elif section.startswith("2"):
    render_clanovi_section()
else:
    st.info("Ovaj odjeljak će biti dodan u sljedećim koracima.")
