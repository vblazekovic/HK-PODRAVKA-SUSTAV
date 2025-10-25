
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
else:
    st.info("Ovaj odjeljak će biti dodan u sljedećim koracima. Trenutno je aktivna Sekcija 1 — Osnovni podaci o klubu.")
# ========================== SEKCIJA 2 — ČLANOVI ==========================

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.lib import utils

# ------- Model & init -------
def _init_members_state():
    ss = st.session_state
    if "members" not in ss:
        ss.members = []  # list of dict
    if "groups" not in ss:
        # početne grupe (možeš mijenjati)
        ss.groups = ["Početnici", "U11", "U13", "U15", "U17", "U20", "Seniori", "Veterani", "Dječice"]
    if "member_edit_index" not in ss:
        ss.member_edit_index = None

# ------- PDF helpers -------
def _make_pdf(bytes_io, title, header_lines, body_text):
    doc = SimpleDocTemplate(bytes_io, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 8))

    for line in header_lines:
        story.append(Paragraph(line, styles["Normal"]))
    story.append(Spacer(1, 10))

    # dugački tekst u jednom komadu
    for para in body_text.split("\n\n"):
        story.append(Paragraph(para.strip().replace("\n", "<br/>"), styles["Normal"]))
        story.append(Spacer(1, 6))

    doc.build(story)
    bytes_io.seek(0)
    return bytes_io

def _pdf_pristupnica(member):
    header = [
        f"Ime i prezime: <b>{member.get('ime_prezime','')}</b>",
        f"Datum rođenja: <b>{member.get('datum_rodenja','')}</b>",
        f"OIB: <b>{member.get('oib','')}</b>",
    ]
    # Tekst iz zahtjeva (sažeto/formatirano za PDF)
    body = (
        "HRVAČKI KLUB „PODRAVKA“, 48000 Koprivnica, Miklinovec 6a, mob:091/456-23-21, "
        "web: www.hk-podravka.hr, e-mail: hsk.podravka@gmail.com.<br/><br/>"
        "OIB:60911784858, žiro-račun: HR6923860021100518154, Podravska banka d.d. Koprivnica.<br/><br/>"
        "<b>STATUT KLUBA - ČLANSTVO</b><br/>"
        "Članom Kluba može postati svaki poslovno sposoban državljanin Republike Hrvatske... "
        "Članom kluba mogu postati i fizičke osobe bez poslovne sposobnosti za koje pristupnicu ispunjava roditelj (staratelj).<br/><br/>"
        "Član se postaje potpisivanjem pristupnice, prihvaćanjem Statuta i upisom u Registar članova, "
        "a odluku o primitku donosi Predsjedništvo. Napomena: Cijeli Statut dostupan je na www.hk-podravka.hr/o-klubu.<br/><br/>"
        "<b>STATUT KLUBA – PRESTANAK ČLANSTVA</b><br/>"
        "Članstvo prestaje: dragovoljnim istupom (istupnica), neplaćanjem članarine duže od šest mjeseci, "
        "isključenjem po odluci Stegovne komisije (uz pravo žalbe Skupštini), gubitkom građanskih prava. "
        "Napomena: Istupnica je dostupna na www.hk-podravka.hr/o-klubu.<br/><br/>"
        "<b>ČLANARINA</b> je obvezujuća tijekom cijele godine (12 mjeseci) i član ju je dužan plaćati "
        "dok ne istupi iz Kluba te dostavi ispunjenu istupnicu.<br/><br/>"
        "<b>IZJAVA O ODGOVORNOSTI</b><br/>"
        "Hrvanje je borilački sport u kojem su moguće ozljede. Suglasni smo da naše dijete pohađa treninge i "
        "da se natječe prema klupskom kalendaru te da ga se fotografira u svrhu stručnih radova i informiranja. "
        "Za eventualne povrede preuzimamo odgovornost. Obvezujemo se u roku 6 mjeseci osigurati odgovarajuću opremu "
        "(patike i dres). Potpisom prihvaćamo načela i Statut Kluba.<br/><br/>"
        "POTPIS ČLANA: ____________________________<br/>"
        "POTPIS RODITELJA/STARATELJA: ____________________________ (za punoljetnog člana nepotreban)"
    )
    buf = BytesIO()
    return _make_pdf(buf, "PRISTUPNICA — HK PODRAVKA", header, body)

def _pdf_privola(member):
    header = [
        f"Član kluba: <b>{member.get('ime_prezime','')}</b>",
        f"OIB: <b>{member.get('oib','')}</b>",
        f"Datum rođenja: <b>{member.get('datum_rodenja','')}</b>",
    ]
    body = (
        "<b>PRIVOLA ZA ZAŠTITU OSOBNIH PODATAKA (GDPR)</b><br/>"
        "Sukladno Zakonu o zaštiti osobnih podataka te Uredbi (EU) 2016/679 (GDPR), "
        "dajem privolu da se moji osobni podaci (ime i prezime, OIB, datum rođenja, adresa, fotografija/video, "
        "kontakt roditelja/staratelja, e-mail, broj putovnice i/ili osobne iskaznice, potvrda o zdravstvenoj sposobnosti, "
        "specifična medicinska stanja, naziv škole/fakulteta) koriste u svrhu vođenja i funkcioniranja Kluba, "
        "prijave i sudjelovanja na natjecanjima te objava na službenim stranicama i društvenim mrežama Kluba i relevantnih sportskih institucija. "
        "Podaci se neće dostavljati trećima bez osnove. Upoznat/a sam s pravima pristupa, ispravka, brisanja, ograničavanja obrade, "
        "prenosivosti te podnošenja prigovora AZOP-u. Privola vrijedi do opoziva i može se povući u bilo kojem trenutku.<br/><br/>"
        "U _____________________________ ; _____________ g.<br/><br/>"
        "Član kluba: _________________________________ (potpis)<br/>"
        "Roditelj/staratelj: _________________________________ (potpis)"
    )
    buf = BytesIO()
    return _make_pdf(buf, "PRIVOLA — HK PODRAVKA", header, body)

# ------- Excel helpers -------
MEMBER_COLUMNS = [
    "ime_prezime","datum_rodenja","spol","oib","mjesto_prebivalista",
    "email_sportasa","email_roditelja","broj_osobne","osobna_vrijedi_do","osobnu_izdao",
    "broj_putovnice","putovnica_vrijedi_do","putovnicu_izdao",
    "aktivni","veteran","ostalo","placa_clanarinu","iznos_clanarine","grupa","napomena"
]

def _members_template_df():
    df = pd.DataFrame(columns=MEMBER_COLUMNS)
    return df

def _download_df_button(df, label, filename):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="clanovi")
    st.download_button(label, data=out.getvalue(), file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def _import_members_from_excel(file):
    try:
        df = pd.read_excel(file)
    except Exception as e:
        st.error(f"Ne mogu pročitati Excel: {e}")
        return 0
    # Normaliziraj kolone
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in MEMBER_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"Nedostaju kolone: {', '.join(missing)}")
        return 0

    added = 0
    for _, row in df.iterrows():
        member = {c: ("" if pd.isna(row.get(c)) else str(row.get(c))) for c in MEMBER_COLUMNS}
        # bool polja
        for b in ["aktivni","veteran","ostalo","placa_clanarinu"]:
            v = str(row.get(b)).strip().lower()
            member[b] = v in ["1","true","da","yes","y","istina"]
        # iznos
        try:
            member["iznos_clanarine"] = float(row.get("iznos_clanarine")) if str(row.get("iznos_clanarine")).strip() not in ["", "nan"] else 30.0
        except:
            member["iznos_clanarine"] = 30.0
        st.session_state.members.append(member)
        added += 1
    return added

# ------- UI helpers -------
def _days_to(date_str):
    if not date_str:
        return None
    try:
        import datetime as _dt
        dt = _dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        return (dt - _dt.date.today()).days
    except:
        return None

def _member_card(member, idx):
    with st.expander(f"{idx+1}. {member.get('ime_prezime','(bez imena)')}", expanded=False):
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            st.write(f"**Datum rođenja:** {member.get('datum_rodenja','')}")
            st.write(f"**Spol:** {member.get('spol','')}")
            st.write(f"**OIB:** {member.get('oib','')}")
            st.write(f"**Mjesto:** {member.get('mjesto_prebivalista','')}")
        with c2:
            st.write(f"**E-mail sportaša:** {member.get('email_sportasa','')}")
            st.write(f"**E-mail roditelja:** {member.get('email_roditelja','')}")
            st.write(f"**Grupa:** {member.get('grupa','')}")
            st.write(f"**Napomena:** {member.get('napomena','')}")
        with c3:
            st.write(f"**Aktivni:** {'DA' if member.get('aktivni') else 'NE'}")
            st.write(f"**Veteran:** {'DA' if member.get('veteran') else 'NE'}")
            st.write(f"**Ostalo:** {'DA' if member.get('ostalo') else 'NE'}")
            if member.get("placa_clanarinu"):
                st.write(f"**Članarina:** DA — {member.get('iznos_clanarine',30)} €")
            else:
                st.write("**Članarina:** NE")

        # Liječnička potvrda status
        lp = member.get("ljecnicka_potvrda_do","")
        days = _days_to(lp)
        if lp:
            if days is not None and days <= 14:
                st.markdown(f"**Liječnička potvrda vrijedi do:** <span class='danger'>{lp} (preostalo {days} dana)</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"**Liječnička potvrda vrijedi do:** <span class='ok'>{lp}</span>", unsafe_allow_html=True)

        # Dokumenti — informativno
        docs = member.get("dokumenti", {})
        if docs:
            st.caption("📎 Dokumenti: " +
                       ", ".join([k for k,v in docs.items() if v]))

        # Akcije
        a1, a2, a3, a4, a5 = st.columns(5)
        with a1:
            if st.button("✏️ Uredi", key=f"edit_{idx}"):
                st.session_state.member_edit_index = idx
                st.experimental_rerun()
        with a2:
            mail_to = member.get("email_sportasa") or member.get("email_roditelja") or ""
            if mail_to:
                st.markdown(f"[📧 Pošalji e-mail]({'mailto:'+mail_to})")
            else:
                st.caption("Nema e-mail adrese")
        with a3:
            # Placeholder akcija
            st.caption("📱 WhatsApp/SMS (ručno)")
        with a4:
            # Generiraj PDF-ove ponovo za preuzimanje
            if st.button("⬇️ Pristupnica PDF", key=f"dl_pr_{idx}"):
                buf = _pdf_pristupnica(member)
                st.download_button("Preuzmi pristupnicu", data=buf.getvalue(),
                                   file_name=f"pristupnica_{member.get('oib','')}.pdf",
                                   mime="application/pdf", key=f"dlbtn_pr_{idx}")
        with a5:
            if st.button("🗑️ Obriši", key=f"del_{idx}"):
                st.session_state.members.pop(idx)
                st.success("Član obrisan.")
                st.experimental_rerun()

# ------- Forme -------
def _member_form(defaults=None):
    d = defaults or {}
    st.markdown("#### ➕ Novi / Uređivanje člana")

    b1, b2, b3 = st.columns(3)
    with b1:
        ime_prezime = st.text_input("Ime i prezime", value=d.get("ime_prezime",""))
        datum_rodenja = st.text_input("Datum rođenja (YYYY-MM-DD)", value=d.get("datum_rodenja",""))
        spol = st.selectbox("Spol", ["","M","Ž"], index=(["","M","Ž"].index(d.get("spol","")) if d.get("spol","") in ["","M","Ž"] else 0))
        oib = st.text_input("OIB", value=d.get("oib",""))
        mjesto = st.text_input("Mjesto prebivališta", value=d.get("mjesto_prebivalista",""))
    with b2:
        email_sportasa = st.text_input("E-mail sportaša", value=d.get("email_sportasa",""))
        email_roditelja = st.text_input("E-mail roditelja", value=d.get("email_roditelja",""))
        br_osobne = st.text_input("Broj osobne iskaznice", value=d.get("broj_osobne",""))
        osobna_do = st.text_input("Osobna vrijedi do (YYYY-MM-DD)", value=d.get("osobna_vrijedi_do",""))
        osobnu_izdao = st.text_input("Osobnu izdao", value=d.get("osobnu_izdao",""))
    with b3:
        br_putovnice = st.text_input("Broj putovnice", value=d.get("broj_putovnice",""))
        putovnica_do = st.text_input("Putovnica vrijedi do (YYYY-MM-DD)", value=d.get("putovnica_vrijedi_do",""))
        putovnicu_izdao = st.text_input("Putovnicu izdao", value=d.get("putovnicu_izdao",""))
        aktivni = st.checkbox("Aktivni natjecatelj/ica", value=bool(d.get("aktivni", False)))
        veteran = st.checkbox("Veteran", value=bool(d.get("veteran", False)))
        ostalo = st.checkbox("Ostalo", value=bool(d.get("ostalo", False)))

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        placa = st.checkbox("Plaća članarinu", value=bool(d.get("placa_clanarinu", False)))
    with c2:
        iznos = st.number_input("Iznos članarine (€)", value=float(d.get("iznos_clanarine", 30.0)), step=5.0, min_value=0.0)
    with c3:
        # grupe
        grp = st.selectbox("Grupa", options=[""] + st.session_state.groups, index= ([""]+st.session_state.groups).index(d.get("grupa","")) if d.get("grupa","") in ([""]+st.session_state.groups) else 0)
        new_grp = st.text_input("Dodaj novu grupu")
        if st.button("➕ Dodaj grupu"):
            g = new_grp.strip()
            if g and g not in st.session_state.groups:
                st.session_state.groups.append(g)
                st.success(f"Dodana grupa: {g}")

    # Fotka (pohrana u RAM-u)
    foto = st.file_uploader("Fotografija člana (opcionalno)", type=["jpg","jpeg","png"])
    if foto:
        st.image(foto, caption="Fotografija (nespremjeno na disk)", use_column_width=True)

    # Liječnička potvrda
    st.markdown("#### 🏥 Liječnička potvrda")
    potv = st.file_uploader("Upload potvrde (PDF/JPG/PNG)", type=["pdf","jpg","jpeg","png"])
    potv_do = st.text_input("Vrijedi do (YYYY-MM-DD)", value=d.get("ljecnicka_potvrda_do",""))
    if potv_do:
        days = _days_to(potv_do)
        if days is not None and days <= 14:
            st.markdown(f"<span class='danger'>Upozorenje: potvrda istječe za {days} dana</span>", unsafe_allow_html=True)

    napomena = st.text_area("Napomena", value=d.get("napomena",""))

    # Spremanje
    submit = st.button("✅ Spremi člana")
    if submit:
        rec = {
            "ime_prezime": ime_prezime,
            "datum_rodenja": datum_rodenja,
            "spol": spol,
            "oib": oib,
            "mjesto_prebivalista": mjesto,
            "email_sportasa": email_sportasa,
            "email_roditelja": email_roditelja,
            "broj_osobne": br_osobne,
            "osobna_vrijedi_do": osobna_do,
            "osobnu_izdao": osobnu_izdao,
            "broj_putovnice": br_putovnice,
            "putovnica_vrijedi_do": putovnica_do,
            "putovnicu_izdao": putovnicu_izdao,
            "aktivni": aktivni,
            "veteran": veteran,
            "ostalo": ostalo,
            "placa_clanarinu": placa,
            "iznos_clanarine": float(iznos if placa else 0.0),
            "grupa": grp,
            "napomena": napomena,
            "dokumenti": {},
            "ljecnicka_potvrda_do": potv_do,
        }
        # spremi dokumente u meta (naziv + timestamp)
        now = datetime.now().isoformat(timespec="seconds")
        if foto:
            rec["dokumenti"]["fotografija"] = f"{foto.name} · {now}"
        if potv:
            rec["dokumenti"]["ljecnicka_potvrda"] = f"{potv.name} · {now}"

        edit_idx = st.session_state.member_edit_index
        if isinstance(edit_idx, int):
            st.session_state.members[edit_idx] = rec
            st.session_state.member_edit_index = None
            st.success("Član ažuriran.")
        else:
            st.session_state.members.append(rec)
            st.success("Član dodan.")

        # automatski generiraj PDF-ove za preuzimanje
        pr_pdf = _pdf_pristupnica(rec)
        st.download_button("⬇️ Preuzmi PRISTUPNICU (PDF)", data=pr_pdf.getvalue(),
                           file_name=f"pristupnica_{oib or ime_prezime}.pdf", mime="application/pdf")

        priv_pdf = _pdf_privola(rec)
        st.download_button("⬇️ Preuzmi PRIVOLU (PDF)", data=priv_pdf.getvalue(),
                           file_name=f"privola_{oib or ime_prezime}.pdf", mime="application/pdf")

        st.stop()  # jasno razdvajanje nakon spremanja

def render_clanovi_section():
    _init_members_state()

    st.markdown("## 👤 ČLANOVI")
    st.caption("Uvoz/izvoz kroz Excel · pojedinačni unos · generiranje PRISTUPNICE i PRIVOLE · status lijev. potvrde.")

    # ====== Excel zona ======
    st.markdown("### 📥 Uvoz / 📤 Izvoz")
    e1, e2, e3 = st.columns([1,1,1])
    with e1:
        _download_df_button(_members_template_df(), "⬇️ Preuzmi Excel predložak", "predlozak_clanovi.xlsx")
    with e2:
        if st.button("⬇️ Preuzmi trenutačne članove (Excel)"):
            if st.session_state.members:
                df = pd.DataFrame(st.session_state.members)
            else:
                df = _members_template_df()
            _download_df_button(df, "Preuzmi datoteku", "clanovi_trenutno.xlsx")
    with e3:
        uploaded = st.file_uploader("⬆️ Uvezi članove iz Excela", type=["xlsx"])
        if uploaded:
            n = _import_members_from_excel(uploaded)
            if n > 0:
                st.success(f"Uvezeno članova: {n}")

    st.markdown("<hr class='brand-hr'/>", unsafe_allow_html=True)

    # ====== Forma za novi/uređivanje ======
    if isinstance(st.session_state.member_edit_index, int):
        st.info(f"Uređivanje člana #{st.session_state.member_edit_index+1}")
        _member_form(st.session_state.members[st.session_state.member_edit_index])
    else:
        _member_form()

    st.markdown("<hr class='brand-hr'/>", unsafe_allow_html=True)

    # ====== Popis članova ======
    st.markdown("### 📚 Popis članova")
    if not st.session_state.members:
        st.caption("Još nema upisanih članova.")
        return

    # Brzi filteri
    f1, f2, f3 = st.columns([1,1,1])
    with f1:
        q = st.text_input("Pretraži po imenu/OIB-u", value="")
    with f2:
        f_grp = st.selectbox("Filtriraj po grupi", options=["(sve)"] + st.session_state.groups, index=0)
    with f3:
        f_aktivni = st.selectbox("Aktivni", ["(svi)","DA","NE"], index=0)

    # Filtriranje
    def _matches(m):
        ok = True
        if q:
            ok = q.lower() in (m.get("ime_prezime","").lower() + " " + m.get("oib","").lower())
        if ok and f_grp != "(sve)":
            ok = (m.get("grupa","") == f_grp)
        if ok and f_aktivni != "(svi)":
            ok = (m.get("aktivni", False) if f_aktivni=="DA" else not m.get("aktivni", False))
        return ok

    for i, m in enumerate([mm for mm in st.session_state.members if _matches(mm)]):
        _member_card(m, i)

# ====================== / SEKCIJA 2 — ČLANOVI ======================

