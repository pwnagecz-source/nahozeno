from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'nahozeno_tajemstvi_2026'
DATA_FILE = 'data.json'

# --- POMOCNÉ FUNKCE PRO DATA ---

def nacti_data():
    vychozi = {
        "nastaveni": {"nazev": "Nahozeno.cz", "slogan": "Tvůj průvodce světem rybaření"},
        "hlavni_clanek": {"nazev": "Zahájení sezóny 2026", "text": "Přípravy vrcholí, pruty jsou připraveny.", "foto": "header.jpg"},
        "novinky": [],
        "uzivatele": [],
        "ulovky": [],
        "reviry": [],
        "akce": [],
        "pocasi": {"teplota": "15°C", "stav": "Polojasno", "tlak": "1013 hPa", "aktivita": "60%"}
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Zajistíme, aby v datech byly všechny klíče
                for klic, hodnota in vychozi.items():
                    if klic not in data:
                        data[klic] = hodnota
                return data
        except:
            return vychozi
    return vychozi

def uloz_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- AUTH (LOGIN / REGISTRACE) ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        obsah = nacti_data()
        jmeno = request.form.get('username')
        heslo = request.form.get('password')
        
        if any(u['jmeno'] == jmeno for u in obsah['uzivatele']) or jmeno.lower() == 'admin':
            return "Jméno je obsazené!"
            
        obsah["uzivatele"].append({"jmeno": jmeno, "heslo": heslo, "role": "user"})
        uloz_data(obsah)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        jmeno = request.form.get('username')
        heslo = request.form.get('password')
        obsah = nacti_data()
        
        # Admin login
        if jmeno == 'admin' and heslo == 'nahozeno2026':
            session['prihlasen'] = True
            session['uzivatel'] = 'Admin'
            session['role'] = 'admin'
            return redirect(url_for('home'))
            
        # User login
        for u in obsah["uzivatele"]:
            if u["jmeno"] == jmeno and u["heslo"] == heslo:
                session['prihlasen'] = True
                session['uzivatel'] = u["jmeno"]
                session['role'] = u.get('role', 'user')
                return redirect(url_for('home'))
        
        return "Chybné jméno nebo heslo!"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- STRÁNKY ---

@app.route('/')
def home():
    # Posíláme celý objekt 'obsah', aby index.html mohl brát počasí i novinky
    return render_template('index.html', obsah=nacti_data())

@app.route('/ulovky', methods=['GET', 'POST'])
def ulovky():
    obsah = nacti_data()
    if request.method == 'POST' and session.get('prihlasen'):
        novy_ulovek = {
            "autor": session['uzivatel'],
            "ryba": request.form.get('ryba'),
            "vaha": request.form.get('vaha'),
            "revir": request.form.get('revir'),
            "foto": request.form.get('foto') or "ryba.jpg",
            "datum": datetime.now().strftime("%d.%m.%Y")
        }
        obsah["ulovky"].insert(0, novy_ulovek)
        uloz_data(obsah)
        return redirect(url_for('ulovky'))
    
    # Sjednocení: Posíláme 'obsah' i sem, aby fungovala navigace a počasí všude stejně
    return render_template('ulovky.html', ulovky=obsah["ulovky"], obsah=obsah)

@app.route('/reviry')
def reviry():
    obsah = nacti_data()
    return render_template('reviry.html', reviry=obsah["reviry"], obsah=obsah)

@app.route('/kalendar')
def kalendar():
    obsah = nacti_data()
    return render_template('kalendar.html', akce=obsah["akce"], obsah=obsah)

@app.route('/clanek/<int:index>')
def detail_clanku(index):
    obsah = nacti_data()
    if 0 <= index < len(obsah["novinky"]):
        clanek = obsah["novinky"][index]
        return render_template('detail.html', clanek=clanek, index=index, obsah=obsah)
    return redirect(url_for('home'))

# --- ADMINISTRACE ---

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('prihlasen') or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    obsah = nacti_data()
    
    if request.method == 'POST':
        akce = request.form.get('akce')
        
        if akce == 'pridat_revir':
            obsah["reviry"].append({
                "nazev": request.form.get('r_nazev'),
                "typ": request.form.get('r_typ'),
                "gps": request.form.get('r_gps'),
                "cislo": request.form.get('r_cislo', '---'),
                "foto": "revir.jpg"
            })
        elif akce == 'pridat_akci':
            obsah["akce"].append({
                "nazev": request.form.get('a_nazev'),
                "datum": request.form.get('a_datum'),
                "popis": request.form.get('a_popis')
            })
        elif akce == 'uprava_pocasi':
            obsah["pocasi"].update({
                "teplota": request.form.get('teplota'),
                "stav": request.form.get('stav'),
                "tlak": request.form.get('tlak'),
                "aktivita": request.form.get('aktivita')
            })
        
        uloz_data(obsah)
        return redirect(url_for('admin'))
    
    return render_template('admin.html', obsah=obsah)

if __name__ == '__main__':
    app.run(debug=True)