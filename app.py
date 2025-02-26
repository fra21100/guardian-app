import streamlit as st
import pandas as pd
import pickle
import plotly.express as px
import requests
import sqlite3
import time
from threading import Thread
import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Carica dataset reale e modello
@st.cache_resource
def initialize_guardian():
    # Carica dataset reale
    df_real = pd.read_csv('creditcard.csv')
    X = df_real.drop(columns=['Time', 'Class'])
    y = df_real['Class']
    # Dividi in train/test (per demo usiamo tutto come test)
    X_test = X
    y_test = y
    try:
        with open('model.pkl', 'rb') as f:
            model = pickle.load(f)
    except:
        model = RandomForestClassifier()
        model.fit(X_test.iloc[:1000], y_test.iloc[:1000])  # Allena su un subset
    return model, X_test, y_test, df_real

# API keys
SHODAN_KEY = os.getenv("SHODAN_KEY", "HWr3qeGqlCVxTqbTmuJX3IgKhTJHW6Lr")
ABUSEIPDB_KEY = os.getenv("ABUSEIPDB_KEY", "c87a09395a0d25e07c20c4c953624bf5efa17d21b6cbad921d1bc0d9e79a7f15894aafb4cd4dd726")

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

# Monitoraggio con dataset reale
def monitor_transactions(model, conn, df_real):
    idx = 0
    while True:
        # Prendi una transazione reale
        transazione = df_real.iloc[idx % len(df_real)][['V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10', 
                                                        'V11', 'V12', 'V13', 'V14', 'V15', 'V16', 'V17', 'V18', 'V19', 
                                                        'V20', 'V21', 'V22', 'V23', 'V24', 'V25', 'V26', 'V27', 'V28', 
                                                        'Amount']].tolist()
        ip = f"192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}"
        previsione = model.predict([transazione[:-1]])[0]
        
        c = conn.cursor()
        c.execute("INSERT INTO transazioni VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                  transazione + [previsione, ip])
        conn.commit()
        
        if previsione == 1:
            model.fit([transazione[:-1]], [previsione])
        time.sleep(1)  # Più veloce per demo
        idx += 1

# Inizializzazione
model, X_test, y_test, df_real = initialize_guardian()
conn = sqlite3.connect('guardian_data.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transazioni 
             (v1 REAL, v2 REAL, v3 REAL, v4 REAL, v5 REAL, v6 REAL, v7 REAL, v8 REAL, 
              v9 REAL, v10 REAL, v11 REAL, v12 REAL, v13 REAL, v14 REAL, v15 REAL, 
              v16 REAL, v17 REAL, v18 REAL, v19 REAL, v20 REAL, v21 REAL, v22 REAL, 
              v23 REAL, v24 REAL, v25 REAL, v26 REAL, v27 REAL, v28 REAL, amount REAL, fraud_class INTEGER, ip TEXT)''')

monitor_thread = Thread(target=monitor_transactions, args=(model, conn, df_real), daemon=True)
monitor_thread.start()

# Interfaccia Streamlit
st.title("GUARDIAN - L’Agente Digitale H24")
st.write("Un guardiano autonomo che protegge la tua banca, sempre.")
st.write(f"Accuratezza attuale: {model.score(X_test, y_test)*100:.2f}%")

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
        dark_web_data = check_dark_web("test@cliente.com")
        if shodan_data and shodan_data.get('ports'):
            st.write(f"Porte sospette: {shodan_data['ports']}")
        if dark_web_data:
            st.warning(f"Dark Web alert: compromessa in {len(dark_web_data)} violazioni")
    else:
        st.success("Transazione sicura.")

st.subheader("Dashboard H24")
df = pd.read_sql_query("SELECT * FROM transazioni ORDER BY ROWID DESC LIMIT 10", conn)
st.dataframe(df)
if not df.empty:
    try:
        fig = px.bar(df, x="ip", y="amount", color="fraud_class", title="Ultime transazioni",
                     color_discrete_map={0: "#33FF57", 1: "#FF5733"})
        st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Errore nel grafico: {str(e)}")
else:
    st.write("Nessuna transazione registrata ancora.")

conn.close()
