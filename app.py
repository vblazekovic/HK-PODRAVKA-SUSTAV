
# app.py — Streamlit verzija Sekcija 1 (Klub) i 2 (Članovi)
import os, json, datetime
from pathlib import Path
from io import BytesIO
import streamlit as st
from openpyxl import Workbook, load_workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --------------------- Inicijalizacija ---------------------
st.set_page_config(page_title="HK Podravka – Admin", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
DOCS_DIR = UPLOAD_DIR / "docs"
IMG_DIR = UPLOAD_DIR / "images"
MEMBER_DIR = UPLOAD_DIR / "members"
for p in [DATA_DIR, UPLOAD_DIR, DOCS_DIR, IMG_DIR, MEMBER_DIR]:
    p.mkdir(parents=True, exist_ok=True)

CLUB_JSON = DATA_DIR / "club.json"
MEMBERS_JSON = DATA_DIR / "members.json"

ALLOWED_DOC = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png"}
ALLOWED_IMG = {".jpg", ".jpeg", ".png", ".svg", ".webp"}

def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except:
            return default
    return default

def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_club():
    return load_json(CLUB_JSON, {
        "naziv": "HRVAČKI KLUB PODRAVKA",
        "ulica_broj": "Miklinovec 6a",
        "grad_postanski": "48000 Koprivnica",
        "oib": "60911784858",
        "iban": "HR6923860021100518154",
        "email": "hsk-podravka@gmail.com",
        "web": "https://hk-podravka.com",
        "social": {"instagram": "", "facebook": "", "tiktok": ""},
        "logo_path": "",
        "predsjednik": {"ime_prezime": "", "telefon": "", "email": ""},
        "tajnik": {"ime_prezime": "", "telefon": "", "email": ""},
        "predsjednistvo": [],
        "nadzorni_odbor": [],
        "statut_path": "",
        "ostali_dokumenti": []
    })

def save_club(data): save_json(CLUB_JSON, data)

def load_members():
    return load_json(MEMBERS_JSON, {"seq": 1, "items": []})

def save_members(d): save_json(MEMBERS_JSON, d)

def new_member_id(members):
    mid = members["seq"]; members["seq"] += 1; return mid

def safe_save(file, target_dir: Path):
    if not file: return ""
    name = Path(file.name)
    ext = name.suffix.lower()
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = f"{name.stem}_{stamp}{ext}"
    out = target_dir / safe
    out.write_bytes(file.read())
    sub = "images" if target_dir == IMG_DIR else ("members" if target_dir == MEMBER_DIR else "docs")
    return str(out)  # vraćamo putanju na disku; za download ćemo čitati i nuditi dugme

def parse_date(s):
    try: return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except: return None

def days_to(date_val):
    if not date_val: return None
    return (date_val - datetime.date.today()).days

# -------- PDF generiranje --------
def gen_pristupnica_pdf(member):
    path = MEMBER_DIR / f"pristupnica_{member['id']}.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4; top = h - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, top, "PRISTUPNICA – HRVAČKI KLUB PODRAVKA")
    c.setFont("Helvetica", 11)
    c.drawString(40, top-20, f"Ime i prezime: {member.get('ime_prezime','')}")
    c.drawString(40, top-38, f"Datum rođenja: {member.get('datum_rodjenja','')}")
    c.drawString(40, top-56, f"OIB: {member.get('oib','')}")
    text = c.beginText(40, top-90); text.setFont("Helvetica", 10)
    paragraf = (
        "HRVAČKI KLUB „PODRAVKA“ 48000 Koprivnica, Miklinovec 6a, mob:091/456-23-21 "
        "web: www.hk-podravka.hr, e-mail: hsk.podravka@gmail.com\n\n"
        "OIB:60911784858, žiro-račun: HR6923860021100518154\n\n"
        "STATUT KLUBA - ČLANSTVO (čl. 14)... Cijeli Statut: www.hk-podravka.hr/o-klubu\n\n"
        "PRESTANAK ČLANSTVA (čl. 21)... Istupnica: www.hk-podravka.hr/o-klubu\n\n"
        "ČLANARINA JE OBVEZUJUĆA TIJEKOM CIJELE GODINE (12 MJESECI)...\n\n"
        "IZJAVA O ODGOVORNOSTI – Hrvanje je borilački sport... Svojim potpisom suglasni smo...\n\n"
        "POTPIS ČLANA: ______________________    POTPIS RODITELJA: ______________________\n"
    )
    for line in paragraf.split("\n"):
        text.textLine(line)
    c.drawText(text); c.showPage(); c.save()
    return str(path)

def gen_privola_pdf(member):
    path = MEMBER_DIR / f"privola_{member['id']}.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4; y = h - 40
    c.setFont("Helvetica-Bold", 14); c.drawString(40, y, "PRIVOLA – obrada osobnih podataka (GDPR)")
    y -= 24; c.setFont("Helvetica", 10); text = c.beginText(40, y)
    paragraf = (
        "Sukladno Zakonu i Uredbi (EU) 2016/679 (GDPR) dajem privolu da se moji podaci koriste "
        "u svrhu vođenja Kluba i prijava na natjecanja, te objava na službenim stranicama i društvenim mrežama Kluba i nadležnih tijela.\n\n"
        "U _____________________________ ; _____________ 20____\n"
        f"Član kluba: {member.get('ime_prezime','')}\n"
        "Potpis: ____________________\n"
        "Roditelj/staratelj (ako je maloljetan): ____________________  Potpis: ____________________\n"
    )
    for line in paragraf.split("\n"):
        text.textLine(line)
    c.drawText(text); c.showPage(); c.save()
    return str(path)

# --------------------- UI ---------------------
st.markdown(
    """
    <style>
    :root{ --primary:#d90429; --accent:#c9a227; }
    .stButton>button{ background:var(--primary); color:white; border:0; }
    .accent{ color:var(--accent); }
    </style>
    """, unsafe_allow_html=True
)

tabs = st.tabs(["🏛️ Klub (Sekcija 1)", "👥 Članovi (Sekcija 2)"])

# ===================== SEKCIJA 1 =====================
with tabs[0]:
    st.subheader("Osnovni podaci o klubu")
    club = load_club()

    colL, colR = st.columns([2,1])
    with colL:
        st.markdown(f"**{club['naziv']}**  \n{club['ulica_broj']}, {club['grad_postanski']}  \nOIB: {club['oib']} · IBAN: {club['iban']}")
    with colR:
        if club.get("logo_path") and Path(club["logo_path"]).exists():
            st.image(club["logo_path"], caption="Logo kluba", use_column_width=True)

    with st.form("frm_club"):
        c1, c2 = st.columns(2)
        with c1:
            club["naziv"] = st.text_input("Naziv kluba", club["naziv"])
            club["ulica_broj"] = st.text_input("Ulica i kućni broj", club["ulica_broj"])
            club["oib"] = st.text_input("OIB", club["oib"])
            club["email"] = st.text_input("E-mail", club["email"])
            club["social"]["instagram"] = st.text_input("Instagram URL", club["social"]["instagram"])
            club["social"]["tiktok"] = st.text_input("TikTok URL", club["social"]["tiktok"])
        with c2:
            logo_f = st.file_uploader("Logo (jpg/png/svg/webp)", type=[e.replace(".","") for e in ALLOWED_IMG])
            club["grad_postanski"] = st.text_input("Grad i poštanski broj", club["grad_postanski"])
            club["iban"] = st.text_input("IBAN", club["iban"])
            club["web"] = st.text_input("Web stranica", club["web"])
            club["social"]["facebook"] = st.text_input("Facebook URL", club["social"]["facebook"])

        st.markdown("### Vodstvo kluba")
        pcol1, pcol2, pcol3 = st.columns(3)
        with pcol1:
            club["predsjednik"]["ime_prezime"] = st.text_input("Predsjednik – Ime i prezime", club["predsjednik"]["ime_prezime"])
            club["tajnik"]["ime_prezime"] = st.text_input("Tajnik – Ime i prezime", club["tajnik"]["ime_prezime"])
        with pcol2:
            club["predsjednik"]["telefon"] = st.text_input("Predsjednik – Kontakt", club["predsjednik"]["telefon"])
            club["tajnik"]["telefon"] = st.text_input("Tajnik – Kontakt", club["tajnik"]["telefon"])
        with pcol3:
            club["predsjednik"]["email"] = st.text_input("Predsjednik – E-mail", club["predsjednik"]["email"])
            club["tajnik"]["email"] = st.text_input("Tajnik – E-mail", club["tajnik"]["email"])

        st.markdown("#### Članovi predsjedništva")
        p_count = st.number_input("Broj članova predsjedništva", min_value=0, value=max(1, len(club["predsjednistvo"]) or 1), step=1)
        pres = club["predsjednistvo"] + [{}]*max(0, p_count - len(club["predsjednistvo"]))
        new_pres = []
        for i in range(int(p_count)):
            a,b,c = st.columns(3)
            with a:
                ime = st.text_input(f"[P{i+1}] Ime i prezime", pres[i].get("ime_prezime",""))
            with b:
                tel = st.text_input(f"[P{i+1}] Kontakt", pres[i].get("telefon",""))
            with c:
                eml = st.text_input(f"[P{i+1}] E-mail", pres[i].get("email",""))
            if any([ime,tel,eml]): new_pres.append({"ime_prezime": ime, "telefon": tel, "email": eml})
        club["predsjednistvo"] = new_pres

        st.markdown("#### Nadzorni odbor")
        n_count = st.number_input("Broj članova nadzornog odbora", min_value=0, value=max(1, len(club["nadzorni_odbor"]) or 1), step=1)
        nad = club["nadzorni_odbor"] + [{}]*max(0, n_count - len(club["nadzorni_odbor"]))
        new_nad = []
        for i in range(int(n_count)):
            a,b,c = st.columns(3)
            with a:
                ime = st.text_input(f"[N{i+1}] Ime i prezime", nad[i].get("ime_prezime",""))
            with b:
                tel = st.text_input(f"[N{i+1}] Kontakt", nad[i].get("telefon",""))
            with c:
                eml = st.text_input(f"[N{i+1}] E-mail", nad[i].get("email",""))
            if any([ime,tel,eml]): new_nad.append({"ime_prezime": ime, "telefon": tel, "email": eml})
        club["nadzorni_odbor"] = new_nad

        st.markdown("### Dokumenti")
        statut_f = st.file_uploader("Statut (PDF)", type=["pdf"])
        ostali_f = st.file_uploader("Ostali dokumenti", type=[e.replace(".","") for e in ALLOWED_DOC], accept_multiple_files=True)

        saved = st.form_submit_button("💾 Spremi")
        if saved:
            if logo_f: club["logo_path"] = safe_save(logo_f, IMG_DIR)
            if statut_f: club["statut_path"] = safe_save(statut_f, DOCS_DIR)
            if ostali_f:
                arr = club.get("ostali_dokumenti", [])
                for f in ostali_f:
                    arr.append(safe_save(f, DOCS_DIR))
                club["ostali_dokumenti"] = arr
            save_club(club)
            st.success("Osnovni podaci spremljeni.")

    st.markdown("**Pregled spremljenih dokumenata**")
    if club.get("statut_path") and Path(club["statut_path"]).exists():
        with open(club["statut_path"], "rb") as fh:
            st.download_button("📥 Preuzmi Statut", data=fh.read(), file_name=Path(club["statut_path"]).name)
    if club.get("ostali_dokumenti"):
        for p in club["ostali_dokumenti"]:
            pth = Path(p)
            if pth.exists():
                with open(pth, "rb") as fh:
                    st.download_button(f"📥 {pth.name}", data=fh.read(), file_name=pth.name, key=f"dl_{pth.name}")

# ===================== SEKCIJA 2 =====================
with tabs[1]:
    st.subheader("Članovi")

    members = load_members()

    with st.expander("➕ Dodaj/uredi člana", expanded=True):
        with st.form("frm_member"):
            c1,c2,c3 = st.columns(3)
            with c1:
                ime = st.text_input("Ime i prezime")
                dat = st.date_input("Datum rođenja", format="YYYY-MM-DD")
                spol = st.selectbox("Spol", ["","m","ž"], index=0)
                oib = st.text_input("OIB")
                mjesto = st.text_input("Mjesto prebivališta")
                slika_f = st.file_uploader("Fotografija", type=[e.replace(".","") for e in ALLOWED_IMG])
            with c2:
                em_s = st.text_input("E-mail sportaša")
                em_r = st.text_input("E-mail roditelja")
                osob_br = st.text_input("Osobna iskaznica – broj")
                osob_vd = st.date_input("Osobna vrijedi do", value=None, format="YYYY-MM-DD")
                osob_izd = st.text_input("Osobnu izdao")
                prist_upl = st.file_uploader("Pristupnica (upload)", type=[e.replace(".","") for e in ALLOWED_DOC])
                priv_upl = st.file_uploader("Privola (upload)", type=[e.replace(".","") for e in ALLOWED_DOC])
            with c3:
                put_br = st.text_input("Putovnica – broj")
                put_vd = st.date_input("Putovnica vrijedi do", value=None, format="YYYY-MM-DD")
                put_izd = st.text_input("Putovnicu izdao")
                grupa = st.selectbox("Grupa", ["","Hrvači","Hrvačice","Veterani","Ostalo"])
                aktivan = st.checkbox("Aktivni natjecatelj/ica", value=False)
                veteran = st.checkbox("Veteran", value=False)
                ostalo = st.checkbox("Ostalo", value=False)
                placa = st.checkbox("Plaća članarinu", value=True)
                iznos = st.number_input("Iznos članarine (€)", min_value=0.0, value=30.0, step=1.0)
                lij_vd = st.date_input("Liječnička vrijedi do", value=None, format="YYYY-MM-DD")
                lij_upl = st.file_uploader("Liječnička potvrda (upload)", type=[e.replace(".","") for e in ALLOWED_DOC])

            submit = st.form_submit_button("💾 Spremi člana")
            if submit:
                mid = new_member_id(members)
                mem = {
                    "id": mid,
                    "ime_prezime": ime.strip(),
                    "datum_rodjenja": dat.isoformat() if dat else "",
                    "spol": spol or "",
                    "oib": oib.strip(),
                    "mjesto": mjesto.strip(),
                    "email_sportas": em_s.strip(),
                    "email_roditelj": em_r.strip(),
                    "osobna_broj": osob_br.strip(),
                    "osobna_vrijedi_do": osob_vd.isoformat() if osob_vd else "",
                    "osobna_izdao": osob_izd.strip(),
                    "putovnica_broj": put_br.strip(),
                    "putovnica_vrijedi_do": put_vd.isoformat() if put_vd else "",
                    "putovnica_izdao": put_izd.strip(),
                    "aktivan_natjecatelj": bool(aktivan),
                    "veteran": bool(veteran),
                    "ostalo": bool(ostalo),
                    "placa_clanarinu": bool(placa),
                    "iznos_clanarine": float(iznos),
                    "grupa": grupa or "",
                    "slika_path": "",
                    "pristupnica_pdf": "",
                    "privola_pdf": "",
                    "pristupnica_upload": "",
                    "privola_upload": "",
                    "lijecnicka_upload": "",
                    "lijecnicka_vrijedi_do": lij_vd.isoformat() if lij_vd else "",
                    "datum_pristupa": datetime.date.today().isoformat(),
                }
                if slika_f: mem["slika_path"] = safe_save(slika_f, MEMBER_DIR)
                if prist_upl: mem["pristupnica_upload"] = safe_save(prist_upl, MEMBER_DIR)
                if priv_upl: mem["privola_upload"] = safe_save(priv_upl, MEMBER_DIR)
                if lij_upl: mem["lijecnicka_upload"] = safe_save(lij_upl, MEMBER_DIR)

                members["items"].append(mem)
                save_members(members)

                # Generiraj PDF-ove
                mem["pristupnica_pdf"] = gen_pristupnica_pdf(mem)
                mem["privola_pdf"] = gen_privola_pdf(mem)
                save_members(members)

                st.success("Član spremljen. Generirane su PDF Pristupnica i Privola.")

    st.markdown("---")
    # Predložak i uvoz/izvoz Excela
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("📄 Preuzmi Excel predložak"):
            wb = Workbook(); ws = wb.active; ws.title = "Clanovi"
            headers = [
                "ime_prezime","datum_rodjenja(YYYY-MM-DD)","spol(m/ž)","oib","mjesto",
                "email_sportas","email_roditelj",
                "osobna_broj","osobna_vrijedi_do(YYYY-MM-DD)","osobna_izdao",
                "putovnica_broj","putovnica_vrijedi_do(YYYY-MM-DD)","putovnica_izdao",
                "aktivan_natjecatelj(da/ne)","veteran(da/ne)","ostalo(da/ne)",
                "placa_clanarinu(da/ne)","iznos_clanarine(decimal)","grupa",
                "lijecnicka_vrijedi_do(YYYY-MM-DD)"
            ]
            ws.append(headers)
            bio = BytesIO(); wb.save(bio); bio.seek(0)
            st.download_button("⬇️ Spremi predložak", data=bio.getvalue(),
                               file_name="predlozak_clanovi.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="dl_tpl")
    with c2:
        upl = st.file_uploader("Uvezi članove (.xlsx)", type=["xlsx"], key="upl_xlsx")
        if upl and st.button("📥 Uvoz .xlsx"):
            wb = load_workbook(upl); ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if rows:
                header = [str(h).strip() if h is not None else "" for h in rows[0]]
                idx = {h:i for i,h in enumerate(header)}
                def val(row, key):
                    i = idx.get(key, None)
                    return (str(row[i]).strip() if i is not None and row[i] is not None else "")
                count=0
                for row in rows[1:]:
                    if not row: continue
                    name = val(row,"ime_prezime")
                    if not name: continue
                    m = {
                        "id": new_member_id(members),
                        "ime_prezime": name,
                        "datum_rodjenja": val(row,"datum_rodjenja(YYYY-MM-DD)") or val(row,"datum_rodjenja"),
                        "spol": val(row,"spol(m/ž)") or val(row,"spol"),
                        "oib": val(row,"oib"),
                        "mjesto": val(row,"mjesto"),
                        "email_sportas": val(row,"email_sportas"),
                        "email_roditelj": val(row,"email_roditelj"),
                        "osobna_broj": val(row,"osobna_broj"),
                        "osobna_vrijedi_do": val(row,"osobna_vrijedi_do(YYYY-MM-DD)") or val(row,"osobna_vrijedi_do"),
                        "osobna_izdao": val(row,"osobna_izdao"),
                        "putovnica_broj": val(row,"putovnica_broj"),
                        "putovnica_vrijedi_do": val(row,"putovnica_vrijedi_do(YYYY-MM-DD)") or val(row,"putovnica_vrijedi_do"),
                        "putovnica_izdao": val(row,"putovnica_izdao"),
                        "aktivan_natjecatelj": (val(row,"aktivan_natjecatelj(da/ne)") or val(row,"aktivan_natjecatelj")).lower()=="da",
                        "veteran": (val(row,"veteran(da/ne)") or val(row,"veteran")).lower()=="da",
                        "ostalo": (val(row,"ostalo(da/ne)") or val(row,"ostalo")).lower()=="da",
                        "placa_clanarinu": (val(row,"placa_clanarinu(da/ne)") or val(row,"placa_clanarinu")).lower()=="da",
                        "iznos_clanarine": float((val(row,"iznos_clanarine(decimal)") or val(row,"iznos_clanarine") or "30").replace(",",".")),
                        "grupa": val(row,"grupa"),
                        "slika_path": "",
                        "pristupnica_pdf": "",
                        "privola_pdf": "",
                        "pristupnica_upload": "",
                        "privola_upload": "",
                        "lijecnicka_upload": "",
                        "lijecnicka_vrijedi_do": val(row,"lijecnicka_vrijedi_do(YYYY-MM-DD)") or "",
                        "datum_pristupa": datetime.date.today().isoformat(),
                    }
                    members["items"].append(m); count+=1
                save_members(members)
                st.success(f"Uvezeno članova: {count}")
    with c3:
        if st.button("📤 Izvoz članova (XLSX)"):
            wb = Workbook(); ws = wb.active; ws.title = "Clanovi"
            headers = [
                "id","ime_prezime","datum_rodjenja","spol","oib","mjesto",
                "email_sportas","email_roditelj",
                "osobna_broj","osobna_vrijedi_do","osobna_izdao",
                "putovnica_broj","putovnica_vrijedi_do","putovnica_izdao",
                "aktivan_natjecatelj","veteran","ostalo",
                "placa_clanarinu","iznos_clanarine","grupa",
                "datum_pristupa","lijecnicka_vrijedi_do"
            ]
            ws.append(headers)
            for m in members["items"]:
                ws.append([
                    m.get("id"), m.get("ime_prezime"), m.get("datum_rodjenja"), m.get("spol"),
                    m.get("oib"), m.get("mjesto"), m.get("email_sportas"), m.get("email_roditelj"),
                    m.get("osobna_broj"), m.get("osobna_vrijedi_do"), m.get("osobna_izdao"),
                    m.get("putovnica_broj"), m.get("putovnica_vrijedi_do"), m.get("putovnica_izdao"),
                    "da" if m.get("aktivan_natjecatelj") else "ne",
                    "da" if m.get("veteran") else "ne",
                    "da" if m.get("ostalo") else "ne",
                    "da" if m.get("placa_clanarinu") else "ne",
                    m.get("iznos_clanarine"),
                    m.get("grupa"),
                    m.get("datum_pristupa"),
                    m.get("lijecnicka_vrijedi_do"),
                ])
            bio = BytesIO(); wb.save(bio); bio.seek(0)
            st.download_button("⬇️ Preuzmi članove", data=bio.getvalue(),
                               file_name="clanovi_izvoz.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="dl_export")

    st.markdown("### Popis članova")
    # Tablica + upozorenja za liječničku
    items = load_members()["items"]
    for m in items:
        m["lij_preostalo"] = days_to(parse_date(m.get("lijecnicka_vrijedi_do")))
    if items:
        for m in sorted(items, key=lambda x: (x.get("ime_prezime",""), x["id"])):
            warn = (m["lij_preostalo"] is not None and m["lij_preostalo"] <= 14)
            with st.container(border=True):
                cols = st.columns([3,2,2,2,3])
                with cols[0]:
                    st.markdown(f"**{m['ime_prezime']}**  \nDOB: {m.get('datum_rodjenja','')}  \nOIB: {m.get('oib','')}")
                    if m.get("slika_path") and Path(m["slika_path"]).exists():
                        st.image(m["slika_path"], width=120)
                with cols[1]:
                    st.markdown(f"Grupa: **{m.get('grupa','—')}**")
                    st.markdown(f"Aktivan: **{'Da' if m.get('aktivan_natjecatelj') else 'Ne'}**")
                    if m.get("placa_clanarinu"):
                        st.markdown(f"Članarina: **{float(m.get('iznos_clanarine') or 0):.2f} €**")
                    else:
                        st.markdown("Članarina: **Ne plaća**")
                with cols[2]:
                    if m.get("lijecnicka_vrijedi_do"):
                        txt = f"Liječnička do: **{m['lijecnicka_vrijedi_do']}**"
                        if warn: txt += f"  \n:warning: Istječe za **{m['lij_preostalo']}** dana"
                        st.markdown(txt)
                    else:
                        st.markdown("Liječnička: —")
                with cols[3]:
                    # download tipke za dokumente ako postoje
                    for key, label in [("pristupnica_pdf","Pristupnica (PDF)"),
                                       ("privola_pdf","Privola (PDF)"),
                                       ("pristupnica_upload","Pristupnica (upl.)"),
                                       ("privola_upload","Privola (upl.)"),
                                       ("lijecnicka_upload","Liječnička (upl.)")]:
                        p = m.get(key)
                        if p and Path(p).exists():
                            with open(p, "rb") as fh:
                                st.download_button(f"📥 {label}", data=fh.read(), file_name=Path(p).name, key=f"{key}_{m['id']}")
                with cols[4]:
                    # brzi "brisanje"
                    if st.button("🗑️ Obriši", key=f"del_{m['id']}"):
                        mem = load_members()
                        mem["items"] = [x for x in mem["items"] if int(x["id"]) != int(m["id"])]
                        save_members(mem)
                        st.rerun()

    else:
        st.info("Još nema unesenih članova.")

# --------------------- Kraj ---------------------


