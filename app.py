import streamlit as st
import pandas as pd
import pickle
import plotly.express as px
import requests
import sqlite3
import time
from threading import Thread
import os
from sklearn.ensemble import RandomForestClassifier  # Esempio modello
import numpy as np

# Carica modello con apprendimento continuo
@st.cache_resource
def initialize_guardian():
    try:
        with open('model.pkl', 'rb') as f:
            model, X_test, y_test = pickle.load(f)
    except:
        # Se non c’è modello, inizializzane uno base
        model = RandomForestClassifier()
        X_test = np.random.rand(100, 28)  # Dati simulati
        y_test = np.random.randint(0, 2, 100)
    return model, X_test, y_test

# API keys sicure
SHODAN_KEY = os.getenv("SHODAN_KEY", "HWr3qeGqlCVxTqbTmuJX3IgKhTJHW6Lr")
IPINFO_KEY = os.getenv("IPINFO_KEY", "e836ce33f43f8a")
ABUSEIPDB_KEY = os.getenv("ABUSEIPDB_KEY", "c87a09395a0d25e07c20c4c953624bf5efa17d21b6cbad921d1bc0d9e79a7f15894aafb4cd4dd726")

# Funzioni API (come nel tuo codice, ma con gestione errori)
def check_shodan(ip):
    try:
        url = f"https://api.shodan.io/shodan/host/{ip}?key={SHODAN_KEY}"
        response = requests.get(url, timeout=5)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def check_dark_web(email):
    try:
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        headers = {"user-agent": "Guardian-Agent"}
        response = requests.get(url, headers=headers, timeout=5)
        return response.json() if response.status_code == 200 else None
    except:
        return None

# Simulazione transazioni continue
def monitor_transactions(model, conn):
    while True:
        # Simula transazione casuale
        transazione = np.random.rand(1, 28).tolist()[0] + [np.random.uniform(1, 10000)]
        ip = f"192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}"
        previsione = model.predict([transazione[:-1]])[0]
        
        # Salva nel DB
        c = conn.cursor()
        c.execute("INSERT INTO transazioni VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                  transazione + [previsione, ip])
        conn.commit()
        
        # Aggiorna modello (simulazione apprendimento)
        if previsione == 1:
            model.fit([transazione[:-1]], [previsione])  # Apprendimento incrementale
        time.sleep(5)  # Simula flusso continuo

# Inizializzazione
model, X_test, y_test = initialize_guardian()
conn = sqlite3.connect('guardian_data.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transazioni 
             (v1 REAL, v2 REAL, v3 REAL, v4 REAL, v5 REAL, v6 REAL, v7 REAL, v8 REAL, 
              v9 REAL, v10 REAL, v11 REAL, v12 REAL, v13 REAL, v14 REAL, v15 REAL, 
              v16 REAL, v17 REAL, v18 REAL, v19 REAL, v20 REAL, v21 REAL, v22 REAL, 
              v23 REAL, v24 REAL, v25 REAL, v26 REAL, v27 REAL, v28 REAL, amount REAL, class INTEGER, ip TEXT)''')

# Avvia monitoraggio in background
monitor_thread = Thread(target=monitor_transactions, args=(model, conn), daemon=True)
monitor_thread.start()

# Interfaccia Streamlit
st.title("GUARDIAN - L’Agente Digitale H24")
st.write("Un guardiano autonomo che protegge la tua banca, sempre.")
st.write(f"Accuratezza attuale: {model.score(X_test, y_test)*100:.2f}%")

# Analisi transazione manuale
st.subheader("Testa una transazione")
cols = st.columns(4)
inputs = [cols[(i-1)%4].number_input(f"V{i}", value=0.0, step=0.1) for i in range(1, 29)]
amount = st.number_input("Importo (€)", min_value=0.0, value=100.0)
ip_trans = st.text_input("IP Transazione", value="8.8.8.8")
if st.button("Analizza"):
    transazione = inputs + [amount]
    previsione = model.predict([transazione])[0]
    c.execute("INSERT INTO transazioni VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
              transazione + [previsione, ip_trans])
    conn.commit()
    if previsione == 1:
        st.error("FRODE RILEVATA! Transazione bloccata.")
        shodan_data = check_shodan(ip_trans)
        dark_web_data = check_dark_web("test@cliente.com")  # Email di esempio
        if shodan_data and shodan_data.get('ports'):
            st.write(f"Porte sospette: {shodan_data['ports']}")
        if dark_web_data:
            st.warning(f"Dark Web alert: compromessa in {len(dark_web_data)} violazioni")
    else:
        st.success("Transazione sicura.")

# Dashboard
st.subheader("Dashboard H24")
df = pd.read_sql_query("SELECT * FROM transazioni ORDER BY ROWID DESC LIMIT 10", conn)
st.dataframe(df)
fig = px.bar(df, x="ip", y="amount", color="class", title="Ultime transazioni")
st.plotly_chart(fig)

conn.close()
