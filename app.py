# -*- coding: utf-8 -*-
"""
HK Podravka – Admin aplikacija (čista verzija v7.1)
Sekcije: Klub, Članovi, Treneri, Natjecanja i rezultati, Statistika
Boje: crvena, bijela, zlatna
"""
import os, io, json, sqlite3
from datetime import date, datetime
import pandas as pd
import streamlit as st

# ---- Boje i osnovni podaci ----
PRIMARY_RED = "#c1121f"
GOLD = "#d4af37"
WHITE = "#ffffff"

KLUB_NAZIV = "Hrvački klub Podravka"
KLUB_EMAIL = "hsk-podravka@gmail.com"
KLUB_ADRESA = "Miklinovec 6a, 48000 Koprivnica"
KLUB_OIB = "60911784858"
KLUB_WEB = "https://hk-podravka.com"
KLUB_IBAN = "HR6923860021100518154"

DB_PATH = "hk_podravka.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---- DB util ----
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # club
    cur.execute("""CREATE TABLE IF NOT EXISTS club_info (
        id INTEGER PRIMARY KEY CHECK (id=1),
        name TEXT, email TEXT, address TEXT, oib TEXT, web TEXT, iban TEXT,
        president TEXT, secretary TEXT, board_json TEXT, supervisory_json TEXT,
        instagram TEXT, facebook TEXT, tiktok TEXT
    )""")
    cur.execute("SELECT 1 FROM club_info WHERE id=1")
    if cur.fetchone() is None:
        cur.execute("""INSERT INTO club_info (id,name,email,address,oib,web,iban,president,secretary,board_json,supervisory_json,instagram,facebook,tiktok)
                       VALUES (1,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (KLUB_NAZIV, KLUB_EMAIL, KLUB_ADRESA, KLUB_OIB, KLUB_WEB, KLUB_IBAN, "", "", "[]", "[]", "", "", ""))
    # members
    cur.execute("""CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT, last_name TEXT, dob TEXT, gender TEXT, oib TEXT UNIQUE,
        street TEXT, city TEXT, postal_code TEXT,
        athlete_email TEXT, parent_email TEXT,
        id_card_number TEXT, id_card_issuer TEXT, id_card_valid_until TEXT,
        passport_number TEXT, passport_issuer TEXT, passport_valid_until TEXT,
        active_competitor INTEGER DEFAULT 0, veteran INTEGER DEFAULT 0, other_flag INTEGER DEFAULT 0,
        pays_fee INTEGER DEFAULT 0, fee_amount REAL DEFAULT 30.0,
        group_name TEXT, photo_path TEXT,
        application_path TEXT, consent_path TEXT,
        medical_path TEXT, medical_valid_until TEXT, consent_checked_date TEXT
    )""")
    # coaches
    cur.execute("""CREATE TABLE IF NOT EXISTS coaches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT, last_name TEXT, dob TEXT, oib TEXT, email TEXT, iban TEXT,
        group_name TEXT, contract_path TEXT, other_docs_json TEXT, photo_path TEXT
    )""")
    # competitions
    cur.execute("""CREATE TABLE IF NOT EXISTS competitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT, kind_other TEXT, name TEXT,
        date_from TEXT, date_to TEXT, place TEXT,
        style TEXT, age_cat TEXT,
        country TEXT, country_iso3 TEXT,
        team_rank INTEGER, club_competitors INTEGER, total_competitors INTEGER,
        clubs_count INTEGER, countries_count INTEGER,
        coaches_json TEXT, notes TEXT, bulletin_url TEXT, website_link TEXT, gallery_paths_json TEXT
    )""")
    # results
    cur.execute("""CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        competition_id INTEGER REFERENCES competitions(id) ON DELETE CASCADE,
        member_id INTEGER REFERENCES members(id) ON DELETE SET NULL,
        category TEXT, style TEXT,
        fights_total INTEGER, wins INTEGER, losses INTEGER, placement INTEGER,
        wins_detail_json TEXT, losses_detail_json TEXT, note TEXT
    )""")
    conn.commit(); conn.close()

# ---- UI util ----
def css_style():
    st.markdown(f"""
    <style>
      .app-header {{background: linear-gradient(90deg,{PRIMARY_RED},{GOLD}); color:{WHITE}; padding:14px 18px; border-radius:14px; margin-bottom:16px;}}
      .stButton>button {{background:{PRIMARY_RED}; color:white; border-radius:10px;}}
    </style>
    """, unsafe_allow_html=True)

def page_header(title, subtitle=None):
    st.markdown(f"<div class='app-header'><h3 style='margin:0'>{title}</h3>{('<div>'+subtitle+'</div>') if subtitle else ''}</div>", unsafe_allow_html=True)

def save_upload(file, subdir):
    if not file: return ""
    path = os.path.join(UPLOAD_DIR, subdir); os.makedirs(path, exist_ok=True)
    fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.name}"
    full = os.path.join(path, fname)
    with open(full, "wb") as f: f.write(file.getbuffer())
    return full

def excel_bytes(df: pd.DataFrame, sheet="Sheet1"):
    out = io.BytesIO()
    # Prefer xlsxwriter if available (for best formatting performance),
    # otherwise safely fall back to openpyxl so the app works even when
    # xlsxwriter isn't installed.
    try:
        import xlsxwriter  # noqa: F401
        engine = "xlsxwriter"
    except Exception:
        engine = "openpyxl"
    with pd.ExcelWriter(out, engine=engine) as w:
        df.to_excel(w, index=False, sheet_name=sheet)
    return out.getvalue()

def mailto(to, subject="", body=""):
    import urllib.parse as up
    q = {}
    if subject: q["subject"]=subject
    if body: q["body"]=body
    qp = up.urlencode(q)
    return f"mailto:{to}?{qp}" if qp else f"mailto:{to}"

# ---- Sekcija 1: Klub ----
def section_club():
    page_header("Klub – osnovni podaci", KLUB_NAZIV)
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM club_info WHERE id=1", conn)
    row = df.iloc[0]
    def _df(js):
        try:
            d = pd.read_json(js)
            if isinstance(d, pd.DataFrame): return d
        except Exception: ...
        return pd.DataFrame(columns=["ime_prezime","telefon","email"])
    board_pref = _df(row.get("board_json","[]"))
    sup_pref = _df(row.get("supervisory_json","[]"))
    with st.form("club_form_v7_1"):
        c1,c2 = st.columns(2)
        name = c1.text_input("KLUB (IME)", row["name"] or "")
        address = c1.text_input("ULICA I KUĆNI BROJ, GRAD I POŠTANSKI BROJ", row["address"] or "")
        email = c1.text_input("E-mail", row["email"] or "")
        web = c1.text_input("Web stranica", row["web"] or "")
        iban = c1.text_input("IBAN račun", row["iban"] or "")
        oib = c1.text_input("OIB", row["oib"] or "")
        president = c2.text_input("Predsjednik kluba", row["president"] or "")
        secretary = c2.text_input("Tajnik kluba", row["secretary"] or "")
        st.markdown("**Članovi predsjedništva** (ime, telefon, e-mail)")
        board = st.data_editor(board_pref if not board_pref.empty else pd.DataFrame(columns=["ime_prezime","telefon","email"]),
                               num_rows="dynamic", key="board_v7_1")
        st.markdown("**Nadzorni odbor** (ime, telefon, e-mail)")
        superv = st.data_editor(sup_pref if not sup_pref.empty else pd.DataFrame(columns=["ime_prezime","telefon","email"]),
                                num_rows="dynamic", key="sup_v7_1")
        s1,s2,s3 = st.columns(3)
        instagram = s1.text_input("Instagram", row["instagram"] or "")
        facebook = s2.text_input("Facebook", row["facebook"] or "")
        tiktok = s3.text_input("TikTok", row["tiktok"] or "")
        st.markdown("**Dokumenti**")
        up_statut = st.file_uploader("Statut (PDF)", type=["pdf"], key="statut_v7_1")
        up_other = st.file_uploader("Ostali dokument (PDF/IMG)", type=["pdf","png","jpg","jpeg"], key="doc_v7_1")
        submitted = st.form_submit_button("Spremi")
    if submitted:
        conn.execute("""UPDATE club_info SET name=?,email=?,address=?,oib=?,web=?,iban=?,president=?,secretary=?,board_json=?,supervisory_json=?,instagram=?,facebook=?,tiktok=? WHERE id=1""",
                     (name,email,address,oib,web,iban,president,secretary,
                      (board if isinstance(board,pd.DataFrame) else pd.DataFrame(board)).to_json(),
                      (superv if isinstance(superv,pd.DataFrame) else pd.DataFrame(superv)).to_json(),
                      instagram,facebook,tiktok))
        conn.execute("""CREATE TABLE IF NOT EXISTS club_docs (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, filename TEXT, path TEXT, uploaded_at TEXT)""")
        if up_statut:
            p = save_upload(up_statut,"club_docs")
            conn.execute("INSERT INTO club_docs(kind,filename,path,uploaded_at) VALUES (?,?,?,?)", ("statut", up_statut.name, p, datetime.now().isoformat()))
        if up_other:
            p = save_upload(up_other,"club_docs")
            conn.execute("INSERT INTO club_docs(kind,filename,path,uploaded_at) VALUES (?,?,?,?)", ("ostalo", up_other.name, p, datetime.now().isoformat()))
        conn.commit(); st.success("Spremljeno.")
    try:
        docs = pd.read_sql_query("SELECT id, kind, filename, uploaded_at FROM club_docs ORDER BY uploaded_at DESC", conn)
        if not docs.empty: st.dataframe(docs, use_container_width=True)
    except Exception:
        pass
    conn.close()

# ---- Sekcija 2: Članovi ----
def members_template_df():
    return pd.DataFrame(columns=[
        "ime","prezime","datum_rodenja(YYYY-MM-DD)","spol(M/Ž)","oib",
        "ulica_i_broj","grad","postanski_broj",
        "email_sportasa","email_roditelja",
        "br_osobne","osobna_vrijedi_do(YYYY-MM-DD)","osobna_izdavatelj",
        "br_putovnice","putovnica_vrijedi_do(YYYY-MM-DD)","putovnica_izdavatelj",
        "aktivni_natjecatelj(0/1)","veteran(0/1)","ostalo(0/1)",
        "placa_clanarinu(0/1)","iznos_clanarine(EUR)","grupa"
    ])

def section_members():
    page_header("Članovi", "Uvoz/izvoz Excel, unos i uređivanje")
    conn = get_conn()
    st.download_button("Predložak (Excel)", data=excel_bytes(members_template_df(),"ClanoviPredlozak"), file_name="predlozak_clanovi.xlsx")
    export_df = pd.read_sql_query("""SELECT first_name AS ime, last_name AS prezime, dob AS datum_rodenja, gender AS spol, oib,
        street AS ulica_i_broj, city AS grad, postal_code AS postanski_broj,
        athlete_email AS email_sportasa, parent_email AS email_roditelja,
        id_card_number AS br_osobne, id_card_valid_until AS osobna_vrijedi_do, id_card_issuer AS osobna_izdavatelj,
        passport_number AS br_putovnice, passport_valid_until AS putovnica_vrijedi_do, passport_issuer AS putovnica_izdavatelj,
        active_competitor AS aktivni_natjecatelj, veteran, other_flag AS ostalo,
        pays_fee AS placa_clanarinu, fee_amount AS iznos_clanarine, group_name AS grupa
        FROM members ORDER BY last_name, first_name""", conn)
    st.download_button("Skini članove (Excel)", data=excel_bytes(export_df,"Clanovi"), file_name="clanovi_export.xlsx", disabled=export_df.empty)

    up_excel = st.file_uploader("Upload članova (Excel po predlošku)", type=["xlsx"], key="members_excel_v7_1")
    if up_excel is not None:
        try:
            df_up = pd.read_excel(up_excel)
            for _, r in df_up.iterrows():
                vals = {
                    "first_name": str(r.get("ime","") or ""),
                    "last_name" : str(r.get("prezime","") or ""),
                    "dob"       : str(r.get("datum_rodenja(YYYY-MM-DD)","") or "")[:10],
                    "gender"    : str(r.get("spol(M/Ž)","") or ""),
                    "oib"       : str(r.get("oib","") or ""),
                    "street"    : str(r.get("ulica_i_broj","") or ""),
                    "city"      : str(r.get("grad","") or ""),
                    "postal"    : str(r.get("postanski_broj","") or ""),
                    "email_s"   : str(r.get("email_sportasa","") or ""),
                    "email_p"   : str(r.get("email_roditelja","") or ""),
                    "id_no"     : str(r.get("br_osobne","") or ""),
                    "id_until"  : str(r.get("osobna_vrijedi_do(YYYY-MM-DD)","") or "")[:10],
                    "id_issuer" : str(r.get("osobna_izdavatelj","") or ""),
                    "pass_no"   : str(r.get("br_putovnice","") or ""),
                    "pass_until": str(r.get("putovnica_vrijedi_do(YYYY-MM-DD)","") or "")[:10],
                    "pass_issuer":str(r.get("putovnica_izdavatelj","") or ""),
                    "active"    : int(r.get("aktivni_natjecatelj(0/1)",0) or 0),
                    "veteran"   : int(r.get("veteran(0/1)",0) or 0),
                    "other"     : int(r.get("ostalo(0/1)",0) or 0),
                    "pays"      : int(r.get("placa_clanarinu(0/1)",0) or 0),
                    "fee"       : float(r.get("iznos_clanarine(EUR)",30) or 30.0),
                    "group"     : str(r.get("grupa","") or ""),
                }
                conn.execute("""
                    INSERT INTO members(first_name,last_name,dob,gender,oib,street,city,postal_code,
                        athlete_email,parent_email,id_card_number,id_card_issuer,id_card_valid_until,
                        passport_number,passport_issuer,passport_valid_until,
                        active_competitor,veteran,other_flag,pays_fee,fee_amount,group_name)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(oib) DO UPDATE SET
                        first_name=excluded.first_name,last_name=excluded.last_name,dob=excluded.dob,gender=excluded.gender,
                        street=excluded.street,city=excluded.city,postal_code=excluded.postal_code,
                        athlete_email=excluded.athlete_email,parent_email=excluded.parent_email,
                        id_card_number=excluded.id_card_number,id_card_issuer=excluded.id_card_issuer,id_card_valid_until=excluded.id_card_valid_until,
                        passport_number=excluded.passport_number,passport_issuer=excluded.passport_issuer,passport_valid_until=excluded.passport_valid_until,
                        active_competitor=excluded.active_competitor,veteran=excluded.veteran,other_flag=excluded.other_flag,
                        pays_fee=excluded.pays_fee,fee_amount=excluded.fee_amount,group_name=excluded.group_name
                """, (vals["first_name"],vals["last_name"],vals["dob"],vals["gender"],vals["oib"],vals["street"],vals["city"],vals["postal"],
                      vals["email_s"],vals["email_p"],vals["id_no"],vals["id_issuer"],vals["id_until"],
                      vals["pass_no"],vals["pass_issuer"],vals["pass_until"],vals["active"],vals["veteran"],vals["other"],vals["pays"],vals["fee"],vals["group"]))
            conn.commit(); st.success("Excel uvoz dovršen.")
        except Exception as e:
            st.error(f"Greška pri uvozu: {e}")

    st.markdown("---"); st.markdown("### Unos novog člana")
    with st.form("member_form_v7_1"):
        c1,c2,c3 = st.columns(3)
        first_name = c1.text_input("Ime"); last_name = c2.text_input("Prezime"); dob = c3.date_input("Datum rođenja", value=date(2010,1,1))
        gender = c1.selectbox("Spol", ["","M","Ž"]); oib = c2.text_input("OIB")
        a1,a2,a3 = st.columns(3); street = a1.text_input("Ulica i kućni broj"); city = a2.text_input("Grad"); postal = a3.text_input("Poštanski broj")
        e1,e2 = st.columns(2); email_s = e1.text_input("E-mail sportaša"); email_p = e2.text_input("E-mail roditelja")
        id1,id2,id3 = st.columns(3); id_no = id1.text_input("Broj osobne"); id_until = id2.date_input("Osobna vrijedi do", value=date.today()); id_issuer = id3.text_input("Izdavatelj osobne")
        p1,p2,p3 = st.columns(3); pass_no = p1.text_input("Broj putovnice"); pass_until = p2.date_input("Putovnica vrijedi do", value=date.today()); pass_issuer = p3.text_input("Izdavatelj putovnice")
        s1,s2,s3 = st.columns(3); active = s1.checkbox("Aktivni natjecatelj/ica"); veteran = s2.checkbox("Veteran"); other = s3.checkbox("Ostalo")
        pays_fee = st.checkbox("Plaća članarinu"); fee_amt = st.number_input("Iznos članarine (EUR)", value=30.0, step=1.0)
        group_name = st.selectbox("Grupa", ["","Hrvači","Hrvačice","Veterani","Ostalo"])
        photo = st.file_uploader("Slika člana", type=["png","jpg","jpeg"])
        app_pdf = st.file_uploader("Pristupnica (PDF)", type=["pdf"]); con_pdf = st.file_uploader("Privola (PDF)", type=["pdf"])
        up_med = st.file_uploader("Liječnička potvrda (PDF/JPG)", type=["pdf","png","jpg","jpeg"]); med_valid = st.date_input("Potvrda vrijedi do", value=date.today())
        submit_member = st.form_submit_button("Spremi člana")
    if submit_member:
        photo_path = save_upload(photo, "members/photos")
        app_path = save_upload(app_pdf, "members/forms")
        con_path = save_upload(con_pdf, "members/forms")
        med_path = save_upload(up_med, "members/medical")
        conn.execute("""
            INSERT INTO members(first_name,last_name,dob,gender,oib,street,city,postal_code,athlete_email,parent_email,
                id_card_number,id_card_issuer,id_card_valid_until,passport_number,passport_issuer,passport_valid_until,
                active_competitor,veteran,other_flag,pays_fee,fee_amount,group_name,photo_path,application_path,consent_path,medical_path,medical_valid_until,consent_checked_date)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(oib) DO UPDATE SET
                first_name=excluded.first_name,last_name=excluded.last_name,dob=excluded.dob,gender=excluded.gender,
                street=excluded.street,city=excluded.city,postal_code=excluded.postal_code,
                athlete_email=excluded.athlete_email,parent_email=excluded.parent_email,
                id_card_number=excluded.id_card_number,id_card_issuer=excluded.id_card_issuer,id_card_valid_until=excluded.id_card_valid_until,
                passport_number=excluded.passport_number,passport_issuer=excluded.passport_issuer,passport_valid_until=excluded.passport_valid_until,
                active_competitor=excluded.active_competitor,veteran=excluded.veteran,other_flag=excluded.other_flag,
                pays_fee=excluded.pays_fee,fee_amount=excluded.fee_amount,group_name=excluded.group_name,
                photo_path=COALESCE(excluded.photo_path,photo_path),
                application_path=COALESCE(excluded.application_path,application_path),
                consent_path=COALESCE(excluded.consent_path,consent_path),
                medical_path=COALESCE(excluded.medical_path,medical_path),
                medical_valid_until=excluded.medical_valid_until,
                consent_checked_date=excluded.consent_checked_date
        """, (first_name,last_name,dob.isoformat(),gender,oib,street,city,postal,email_s,email_p,id_no,id_issuer,id_until.isoformat(),
              pass_no,pass_issuer,pass_until.isoformat(),int(active),int(veteran),int(other),int(pays_fee),float(fee_amt),group_name,
              photo_path,app_path,con_path,med_path,med_valid.isoformat(), datetime.now().date().isoformat()))
        conn.commit(); st.success("Član spremljen.")

    st.markdown("---"); st.markdown("### Popis članova")
    members_df = pd.read_sql_query("""SELECT id, first_name, last_name, gender, dob, oib, street, city, postal_code, athlete_email, parent_email,
        group_name, pays_fee, fee_amount, medical_valid_until FROM members ORDER BY last_name, first_name""", conn)
    if not members_df.empty:
        edited = st.data_editor(members_df, num_rows="dynamic", use_container_width=True, key="members_grid_v7_1")
        c1,c2,c3 = st.columns(3)
        if c1.button("Spremi izmjene"):
            for _, r in edited.iterrows():
                conn.execute("""UPDATE members SET first_name=?,last_name=?,gender=?,dob=?,street=?,city=?,postal_code=?,athlete_email=?,parent_email=?,group_name=?,pays_fee=?,fee_amount=?,medical_valid_until=? WHERE id=?""",
                             (str(r.get("first_name","")),str(r.get("last_name","")),str(r.get("gender","")),str(r.get("dob",""))[:10],
                              str(r.get("street","")),str(r.get("city","")),str(r.get("postal_code","")),
                              str(r.get("athlete_email","")),str(r.get("parent_email","")),
                              str(r.get("group_name","")),int(r.get("pays_fee",0) or 0),float(r.get("fee_amount",0) or 0.0),
                              str(r.get("medical_valid_until","")),int(r["id"])))
            conn.commit(); st.success("Izmjene spremljene.")
        del_id = c2.number_input("ID člana za brisanje", min_value=0, step=1, value=0)
        if c3.button("Obriši člana") and del_id>0:
            conn.execute("DELETE FROM members WHERE id=?", (int(del_id),)); conn.commit(); st.success("Član obrisan."); st.rerun()
    conn.close()

# ---- Sekcija 3: Treneri ----
def section_coaches():
    page_header("Treneri", "Unos trenera, dokumenti i slike")
    conn = get_conn()
    with st.form("coach_form_v7_1"):
        c1,c2,c3 = st.columns(3)
        first_name = c1.text_input("Ime"); last_name = c2.text_input("Prezime"); dob = c3.date_input("Datum rođenja", value=date(1990,1,1))
        oib = c1.text_input("OIB"); email = c2.text_input("E-mail"); iban = c3.text_input("IBAN broj računa")
        group_name = st.text_input("Grupa koju trenira (može se mijenjati)")
        contract = st.file_uploader("Ugovor s klubom (PDF)", type=["pdf"])
        other_docs = st.file_uploader("Drugi dokumenti (višestruko)", type=["pdf","png","jpg","jpeg"], accept_multiple_files=True)
        photo = st.file_uploader("Slika trenera", type=["png","jpg","jpeg"])
        submit = st.form_submit_button("Spremi trenera")
    if submit:
        def up(f, sub): return save_upload(f, sub) if f else ""
        contract_path = up(contract, "coaches/contracts")
        other_paths = [up(f,"coaches/docs") for f in (other_docs or [])]
        photo_path = up(photo, "coaches/photos")
        conn.execute("""INSERT INTO coaches(first_name,last_name,dob,oib,email,iban,group_name,contract_path,other_docs_json,photo_path)
                        VALUES(?,?,?,?,?,?,?,?,?,?)""",
                     (first_name,last_name,dob.isoformat(),oib,email,iban,group_name,contract_path,json.dumps(other_paths),photo_path))
        conn.commit(); st.success("Trener spremljen.")
    st.markdown("---"); st.markdown("### Popis trenera")
    coaches_df = pd.read_sql_query("""SELECT id, first_name, last_name, dob, oib, email, iban, group_name FROM coaches ORDER BY last_name, first_name""", conn)
    if not coaches_df.empty:
        edited = st.data_editor(coaches_df, num_rows="dynamic", use_container_width=True, key="coaches_grid_v7_1")
        c1,c2,c3 = st.columns(3)
        if c1.button("Spremi izmjene (treneri)"):
            for _, r in edited.iterrows():
                conn.execute("""UPDATE coaches SET first_name=?, last_name=?, dob=?, oib=?, email=?, iban=?, group_name=? WHERE id=?""",
                             (str(r.get("first_name","")),str(r.get("last_name","")),str(r.get("dob",""))[:10],str(r.get("oib","")),str(r.get("email","")),str(r.get("iban","")),str(r.get("group_name","")),int(r["id"])))
            conn.commit(); st.success("Izmjene spremljene.")
        del_id = c2.number_input("ID za brisanje", min_value=0, step=1, value=0)
        if c3.button("Obriši trenera") and del_id>0:
            conn.execute("DELETE FROM coaches WHERE id=?", (int(del_id),)); conn.commit(); st.success("Trener obrisan."); st.rerun()
    conn.close()

# ---- Sekcija 4: Natjecanja i rezultati ----
def section_competitions():
    page_header("Natjecanja i rezultati", "Unos natjecanja + rezultata")
    conn = get_conn()
    kind = st.selectbox("Vrsta", ["PRVENSTVO HRVATSKE","MEĐUNARODNI TURNIR","REPREZENTATIVNI NASTUP","HRVAČKA LIGA ZA SENIORE","MEĐUNARODNA HRVAČKA LIGA ZA KADETE","REGIONALNO PRVENSTVO","LIGA ZA DJEVOJČICE","OSTALO"])
    kind_other = st.text_input("Druga vrsta", "") if kind=="OSTALO" else ""
    name = st.text_input("Ime natjecanja (ako postoji)", "")
    c1,c2,c3 = st.columns(3)
    date_from = c1.date_input("Datum od", value=date.today())
    date_to = c2.date_input("Datum do", value=date.today())
    place = c3.text_input("Mjesto")
    style = st.selectbox("Hrvački stil", ["GR","FS","WW","BW","MODIFICIRANO"])
    age = st.selectbox("Uzrast", ["POČETNICI","U11","U13","U15","U17","U20","U23","SENIORI"])
    country = st.text_input("Država"); iso3 = st.text_input("ISO-3 (npr. HRV)")
    n1,n2,n3,n4,n5 = st.columns(5)
    team_rank = n1.number_input("Ekipni poredak", min_value=0, step=1)
    club_n = n2.number_input("Broj klupskih natjecatelja", min_value=0, step=1)
    total_n = n3.number_input("Uk. natjecatelja", min_value=0, step=1)
    clubs_n = n4.number_input("Broj klubova", min_value=0, step=1)
    countries_n = n5.number_input("Broj zemalja", min_value=0, step=1)
    notes = st.text_area("Zapažanje trenera / opis")
    gallery = st.file_uploader("Slike (višestruko)", type=["png","jpg","jpeg"], accept_multiple_files=True)
    bulletin_url = st.text_input("Poveznica na rezultate / bilten"); website_link = st.text_input("Poveznica na objavu na webu")
    if st.button("Spremi natjecanje"):
        paths = [save_upload(f,"competitions/gallery") for f in (gallery or [])]
        conn.execute("""INSERT INTO competitions(kind,kind_other,name,date_from,date_to,place,style,age_cat,country,country_iso3,team_rank,club_competitors,total_competitors,clubs_count,countries_count,coaches_json,notes,bulletin_url,website_link,gallery_paths_json)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                     (kind,kind_other,name,date_from.isoformat(),date_to.isoformat(),place,style,age,country,iso3,int(team_rank),int(club_n),int(total_n),int(clubs_n),int(countries_n),"[]",notes,bulletin_url,website_link,json.dumps(paths)))
        conn.commit(); st.success("Natjecanje spremljeno.")
    st.markdown("---"); st.markdown("### Rezultati")
    comps = pd.read_sql_query("SELECT id, COALESCE(name, kind) AS title, date_from FROM competitions ORDER BY date_from DESC", conn)
    comp_opts = {f"{r['id']} – {r['title']} ({r['date_from']})": r['id'] for _, r in comps.iterrows()}
    comp_sel = st.selectbox("Odaberi natjecanje", options=["-"] + list(comp_opts.keys()))
    mems = pd.read_sql_query("SELECT id, first_name || ' ' || last_name AS full FROM members ORDER BY last_name, first_name", conn)
    mem_opts = {f"{r['id']} – {r['full']}": r['id'] for _, r in mems.iterrows()}
    if comp_sel != "-":
        comp_id = comp_opts[comp_sel]
        mem_sel = st.selectbox("Član", options=["-"] + list(mem_opts.keys()))
        if mem_sel != "-":
            member_id = mem_opts[mem_sel]
            c1,c2,c3 = st.columns(3)
            category = c1.text_input("Kategorija / težina")
            stl = c2.selectbox("Stil", ["GR","FS","WW","BW","MODIFICIRANO"])
            fights = c3.number_input("Ukupno borbi", min_value=0, step=1)
            wins = c1.number_input("Pobjede", min_value=0, step=1)
            losses = c2.number_input("Porazi", min_value=0, step=1)
            placement = c3.number_input("Plasman (1–100)", min_value=0, max_value=100, step=1)
            wins_d = st.text_area("Pobjede – unesite stavke odvojene | (npr. 'Ivo Ivić;HKX | Marko Markić;HKY')")
            losses_d = st.text_area("Porazi – unesite stavke odvojene |")
            note = st.text_area("Napomena trenera")
            if st.button("Spremi rezultat"):
                conn.execute("""INSERT INTO results(competition_id,member_id,category,style,fights_total,wins,losses,placement,wins_detail_json,losses_detail_json,note)
                                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                             (comp_id, member_id, category, stl, int(fights), int(wins), int(losses), int(placement),
                              json.dumps([s for s in wins_d.split('|') if s.strip()]), json.dumps([s for s in losses_d.split('|') if s.strip()]), note))
                conn.commit(); st.success("Rezultat spremljen.")
    year = st.number_input("Godina za izvoz", min_value=2000, max_value=2100, value=datetime.now().year, step=1)
    df = pd.read_sql_query("""SELECT c.date_from, c.kind, c.name, c.place, c.style, c.age_cat, r.member_id,
           (SELECT first_name || ' ' || last_name FROM members m WHERE m.id=r.member_id) AS sportas,
           r.category, r.fights_total, r.wins, r.losses, r.placement
        FROM results r JOIN competitions c ON r.competition_id=c.id WHERE substr(c.date_from,1,4)=?
        ORDER BY c.date_from DESC""", conn, params=(str(year),))
    st.dataframe(df, use_container_width=True)
    st.download_button("Skini rezultate (Excel)", data=excel_bytes(df,"Rezultati"), file_name=f"rezultati_{year}.xlsx", disabled=df.empty)
    conn.close()

# ---- Sekcija 5: Statistika ----
def section_stats():
    page_header("Statistika", "Po godini, vrsti i stilu")
    conn = get_conn()
    year = st.number_input("Godina", min_value=2000, max_value=2100, value=datetime.now().year, step=1, key="stat_year_v7_1")
    df = pd.read_sql_query("""SELECT c.kind, c.age_cat, r.style,
        SUM(r.fights_total) AS borbi, SUM(r.wins) AS pobjede, SUM(r.losses) AS porazi,
        SUM(CASE WHEN r.placement=1 THEN 1 ELSE 0 END) AS zlato,
        SUM(CASE WHEN r.placement=2 THEN 1 ELSE 0 END) AS srebro,
        SUM(CASE WHEN r.placement=3 THEN 1 ELSE 0 END) AS bronca
        FROM competitions c JOIN results r ON r.competition_id=c.id
        WHERE substr(c.date_from,1,4)=?
        GROUP BY c.kind, c.age_cat, r.style
        ORDER BY c.kind, c.age_cat""", conn, params=(str(year),))
    st.dataframe(df, use_container_width=True)
    st.download_button("Skini statistiku (Excel)", data=excel_bytes(df, "Statistika"), file_name=f"stat_{year}.xlsx", disabled=df.empty)
    conn.close()

# ---- App ----
def main():
    st.set_page_config(page_title="HK Podravka – Admin", layout="wide")
    css_style()
    init_db()
    menu = st.sidebar.radio("Izbornik", ["Klub", "Članovi", "Treneri", "Natjecanja i rezultati", "Statistika", "Grupe", "Veterani", "Prisustvo"])
    if menu == "Klub": section_club()
    elif menu == "Članovi": section_members()
    elif menu == "Treneri": section_coaches()
    elif menu == "Natjecanja i rezultati": section_competitions()
    elif menu == "Statistika": section_stats()
    elif menu == "Grupe": section_groups()
    elif menu == "Veterani": section_veterans()
    else: section_attendance()

if __name__ == "__main__":
    main()


def ensure_extra_tables(conn):
    cur = conn.cursor()
    # Grupe
    cur.execute("""CREATE TABLE IF NOT EXISTS groups (
        name TEXT PRIMARY KEY,
        description TEXT DEFAULT ''
    )""")
    # Trening sesije (prisustvo)
    cur.execute("""CREATE TABLE IF NOT EXISTS training_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trainer_id INTEGER,
        trainer_name TEXT,
        group_name TEXT,
        start_dt TEXT,
        end_dt TEXT,
        location TEXT,
        rep_prep INTEGER DEFAULT 0
    )""")
    # Evidencija prisustva po članu
    cur.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        member_id INTEGER,
        present INTEGER DEFAULT 1,
        UNIQUE(session_id, member_id)
    )""")
    conn.commit()


# ---- Sekcija: Grupe ----
def section_groups():
    st.header("Grupe")
    conn = get_conn()
    cur = conn.cursor()
    # Forma za dodavanje/uređivanje grupa
    st.subheader("Popis i uređivanje grupa")
    with st.form("grp_form", clear_on_submit=True):
        col1, col2 = st.columns([2,3])
        with col1:
            g_name = st.text_input("Naziv grupe")
        with col2:
            g_desc = st.text_input("Opis / napomena", "")
        submitted = st.form_submit_button("Spremi grupu")
        if submitted:
            if g_name.strip():
                cur.execute("INSERT OR REPLACE INTO groups (name, description) VALUES (?,?)", (g_name.strip(), g_desc.strip()))
                conn.commit()
                st.success("Grupa spremljena.")
            else:
                st.warning("Upišite naziv grupe.")
    # Popis grupa
    grp_df = pd.read_sql_query("SELECT name AS grupa, description AS opis FROM groups ORDER BY name", conn)
    st.dataframe(grp_df, use_container_width=True)
    st.divider()

    # Dodjela članova u grupe i premještanje
    st.subheader("Članovi i grupe")
    members_df = pd.read_sql_query("SELECT id, first_name || ' ' || last_name AS ime, COALESCE(group_name,'') AS grupa FROM members ORDER BY last_name, first_name", conn)
    all_groups = [""] + [g for g in grp_df["grupa"].tolist()]
    sel_member = st.selectbox("Odaberi člana", options=members_df["ime"].tolist())
    current_group = members_df.loc[members_df['ime']==sel_member, 'grupa'].values[0]
    new_group = st.selectbox("Dodijeli u grupu", options=all_groups, index=all_groups.index(current_group) if current_group in all_groups else 0)
    if st.button("Spremi dodjelu/premještanje"):
        mem_id = int(members_df.loc[members_df['ime']==sel_member, 'id'].values[0])
        cur.execute("UPDATE members SET group_name=? WHERE id=?", (new_group if new_group else None, mem_id))
        conn.commit()
        st.success("Član ažuriran.")
        st.experimental_rerun()

    # Excel export/import grupa
    st.subheader("Excel import/export (grupe)")
    export_df = pd.read_sql_query("SELECT first_name AS ime, last_name AS prezime, COALESCE(group_name,'') AS grupa FROM members ORDER BY last_name, first_name", conn)
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="xlsxwriter") as writer:
        export_df.to_excel(writer, index=False, sheet_name="grupe")
    st.download_button("Skini Excel grupe", data=excel_buf.getvalue(), file_name="grupe_export.xlsx")
    up = st.file_uploader("Upload Excel grupe (kolone: ime, prezime, grupa)", type=["xlsx"], key="grupe_xlsx_up")
    if up is not None:
        try:
            df_up = pd.read_excel(up)
            for _, r in df_up.iterrows():
                g = str(r.get("grupa","") or "").strip()
                ime = str(r.get("ime","")).strip()
                prez = str(r.get("prezime","")).strip()
                if not ime or not prez:
                    continue
                # nađi člana
                row = pd.read_sql_query("SELECT id FROM members WHERE first_name=? AND last_name=? LIMIT 1", conn, params=(ime, prez))
                if not row.empty:
                    mem_id = int(row.iloc[0]["id"])
                    cur.execute("UPDATE members SET group_name=? WHERE id=?", (g if g else None, mem_id))
            conn.commit()
            st.success("Grupe su uvezene.")
        except Exception as e:
            st.error(f"Greška pri uvozu: {e}")


# ---- Sekcija: Veterani ----
def section_veterans():
    st.header("Veterani")
    conn = get_conn()
    # filter veterana
    df = pd.read_sql_query("""
        SELECT id, first_name AS ime, last_name AS prezime, athlete_email AS email, parent_email AS email_roditelja,
               phone AS telefon, group_name AS grupa
        FROM members
        WHERE COALESCE(veteran,0)=1
        ORDER BY last_name, first_name
    """, conn)
    if df.empty:
        st.info("Nema označenih veterana.")
        return
    st.dataframe(df.drop(columns=["id"]), use_container_width=True)
    st.caption("Kliknite na ime u popisu članova za uređivanje u sekciji 'Članovi'.")

    # Masovna obavijest – generiraj mailto i WhatsApp linkove
    st.subheader("Slanje obavijesti")
    emails = [e for e in (df["email"].dropna().tolist() + df["email_roditelja"].dropna().tolist()) if e]
    unique_emails = sorted(set(emails))
    if unique_emails:
        mailto_link = "mailto:" + ",".join(unique_emails)
        st.markdown(f"[Pošalji e-mail svima]({mailto_link})")
    phones = [str(p) for p in df["telefon"].dropna().tolist() if str(p).strip()]
    if phones:
        # WhatsApp bulk open isn't standardized; provide first contact quick link
        wa = f"https://wa.me/{phones[0]}"
        st.markdown(f"[Otvori WhatsApp za prvi broj]({wa})")


# ---- Sekcija: Prisustvo ----
def section_attendance():
    st.header("Prisustvo")
    conn = get_conn()
    cur = conn.cursor()

    # Kreiranje treninga
    st.subheader("Evidencija treninga")
    # Treneri i grupe
    coaches = pd.read_sql_query("SELECT id, first_name || ' ' || last_name AS ime FROM coaches ORDER BY last_name, first_name", conn)
    groups = pd.read_sql_query("SELECT name FROM groups ORDER BY name", conn)
    col = st.columns(2)
    with col[0]:
        trainer_name = st.selectbox("Trener", options=coaches["ime"].tolist() if not coaches.empty else ["-"], index=0)
    with col[1]:
        group_name = st.selectbox("Grupa", options=groups["name"].tolist() if not groups.empty else ["-"], index=0)

    col2 = st.columns(3)
    with col2[0]:
        start_dt = st.datetime_input("Vrijeme početka", value=datetime.datetime.now().replace(minute=0, second=0, microsecond=0))
    with col2[1]:
        end_dt = st.datetime_input("Vrijeme završetka", value=datetime.datetime.now().replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1))
    with col2[2]:
        location = st.text_input("Lokacija", "")

    rep_prep = st.checkbox("Pripreme reprezentacije", value=False)
    if st.button("Spremi trening"):
        if trainer_name == "-" or group_name == "-":
            st.warning("Dodajte trenere i grupe prije spremanja.")
        else:
            # map trainer_name back to id (best-effort)
            trow = coaches.loc[coaches['ime']==trainer_name]
            trainer_id = int(trow['id'].values[0]) if not trow.empty else None
            cur.execute("""INSERT INTO training_sessions (trainer_id, trainer_name, group_name, start_dt, end_dt, location, rep_prep)
                           VALUES (?,?,?,?,?,?,?)""",
                        (trainer_id, trainer_name, group_name, start_dt.isoformat(), end_dt.isoformat(), location, 1 if rep_prep else 0))
            conn.commit()
            st.success("Trening je spremljen.")

    st.divider()

    # Označavanje prisustva po treningu
    st.subheader("Označavanje prisustva")
    sessions = pd.read_sql_query("SELECT id, date(start_dt) AS datum, time(start_dt) AS od, time(end_dt) AS do, group_name, trainer_name, location FROM training_sessions ORDER BY start_dt DESC LIMIT 50", conn)
    if sessions.empty:
        st.info("Još nema treninga.")
        return
    row_label = sessions.apply(lambda r: f"{r['datum']} {r['od'][:-3]}-{r['do'][:-3]} • {r['group_name']} ({r['trainer_name']})", axis=1).tolist()
    idx = st.selectbox("Odaberi trening", options=list(range(len(row_label))), format_func=lambda i: row_label[i] if 0 <= i < len(row_label) else "")
    sel_session = int(sessions.iloc[idx]["id"])

    # Članovi u grupi (plus ručno dodavanje)
    grp = sessions.iloc[idx]["group_name"]
    members = pd.read_sql_query("SELECT id, first_name || ' ' || last_name AS ime FROM members WHERE group_name=? ORDER BY last_name, first_name", conn, params=(grp,))
    extra_member = st.text_input("Dodaj člana iz druge grupe (ime i prezime, točan zapis)")
    if st.button("Dodaj dodatnog člana"):
        if extra_member.strip():
            row = pd.read_sql_query("SELECT id FROM members WHERE first_name || ' ' || last_name = ? LIMIT 1", conn, params=(extra_member.strip(),))
            if not row.empty:
                mem_id = int(row.iloc[0]["id"])
                cur.execute("INSERT OR IGNORE INTO attendance (session_id, member_id, present) VALUES (?,?,1)", (sel_session, mem_id))
                conn.commit()
                st.success("Član dodan.")
            else:
                st.warning("Član nije pronađen.")

    # Popis i kvačice prisustva
    att_df = pd.read_sql_query("""
        SELECT m.id AS member_id, m.first_name || ' ' || m.last_name AS ime,
               COALESCE(a.present, 0) AS prisutan
        FROM members m
        LEFT JOIN attendance a ON a.member_id = m.id AND a.session_id = ?
        WHERE m.group_name=?
        ORDER BY m.last_name, m.first_name
    """, conn, params=(sel_session, grp))
    for _, r in att_df.iterrows():
        val = st.checkbox(r["ime"], value=bool(r["prisutan"]))
        # write through on toggle
        cur.execute("INSERT OR IGNORE INTO attendance (session_id, member_id, present) VALUES (?,?,?)", (sel_session, int(r["member_id"]), 1 if val else 0))
        cur.execute("UPDATE attendance SET present=? WHERE session_id=? AND member_id=?", (1 if val else 0, sel_session, int(r["member_id"])))
    conn.commit()

    st.divider()
    # Statistika po mjesecima
    st.subheader("Statistika (mjesec)")
    year = st.number_input("Godina", min_value=2020, max_value=datetime.datetime.now().year, value=datetime.datetime.now().year, step=1)
    month = st.number_input("Mjesec", min_value=1, max_value=12, value=datetime.datetime.now().month, step=1)
    stats_df = pd.read_sql_query("""
        SELECT date(start_dt) AS datum,
               CAST((julianday(end_dt) - julianday(start_dt)) * 24.0 AS REAL) AS sati
        FROM training_sessions
        WHERE strftime('%Y', start_dt)=? AND strftime('%m', start_dt)=?
        ORDER BY start_dt
    """, conn, params=(str(year), f"{int(month):02d}"))
    total_sessions = len(stats_df)
    total_hours = round(stats_df["sati"].sum(), 2) if not stats_df.empty else 0.0
    st.metric("Broj treninga", total_sessions)
    st.metric("Sati", total_hours)
