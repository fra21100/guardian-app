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

# Funzione per scaricare il file da GitHub Releases
def download_file(url, dest):
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, stream=True)
    r.raise_for_status()
    with open(dest, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    file_size = os.path.getsize(dest)
    st.write(f"Dimensione file scaricato: {file_size} byte")
    with open(dest, 'rb') as f:
        first_bytes = f.read(100)
        if first_bytes.startswith(b'<!DOCTYPE html'):
            raise ValueError("Il file scaricato è una pagina HTML, non un CSV.")
        st.write(f"Primi 100 byte: {first_bytes[:50].decode('utf-8', errors='ignore')}")

@st.cache_resource
def initialize_guardian():
    dataset_path = 'creditcard.csv'
    github_url = 'https://github.com/fra21100/guardian-app/releases/download/v1.0.0/creditcard.csv'
    
    if not os.path.exists(dataset_path):
        st.write("Scaricamento del dataset da GitHub Releases in corso...")
        try:
            download_file(github_url, dataset_path)
            st.write("Download completato!")
        except Exception as e:
            st.error(f"Errore nel download: {str(e)}")
            raise
    
    with open(dataset_path, 'rb') as f:
        first_line = f.readline().decode('utf-8', errors='ignore')
        st.write(f"Anteprima file: {first_line[:50]}")
    
    try:
        df_real = pd.read_csv(dataset_path)
    except pd.errors.ParserError as e:
        st.error(f"Errore nel parsing del CSV: {str(e)}")
        raise
    
    X = df_real.drop(columns=['Time', 'Class'])
    y = df_real['Class']
    X_test = X
    y_test = y
    try:
        with open('model.pkl', 'rb') as f:
            model = pickle.load(f)
    except:
        model = RandomForestClassifier()
        model.fit(X_test.iloc[:1000], y_test.iloc[:1000])
    return model, X_test, y_test, df_real

# Inizializzazione
model, X_test, y_test, df_real = initialize_guardian()
conn = sqlite3.connect('guardian_data.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transazioni 
             (v1 REAL, v2 REAL, v3 REAL, v4 REAL, v5 REAL, v6 REAL, v7 REAL, v8 REAL, 
              v9 REAL, v10 REAL, v11 REAL, v12 REAL, v13 REAL, v14 REAL, v15 REAL, 
              v16 REAL, v17 REAL, v18 REAL, v19 REAL, v20 REAL, v21 REAL, v22 REAL, 
              v23 REAL, v24 REAL, v25 REAL, v26 REAL, v27 REAL, v28 REAL, amount REAL, fraud_class INTEGER, ip TEXT)''')

def monitor_transactions(model, conn, df_real):
    idx = 0
    while True:
        transazione = df_real.iloc[idx % len(df_real)][['V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10', 
                                                        'V11', 'V12', 'V13', 'V14', 'V15', 'V16', 'V17', 'V18', 'V19', 
                                                        'V20', 'V21', 'V22', 'V23', 'V24', 'V25', 'V26', 'V27', 'V28', 
                                                        'Amount']].tolist()
        ip = f"192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}"
        previsione = model.predict([transazione[:-1]])[0]
        c.execute("INSERT INTO transazioni VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                  transazione + [previsione, ip])
        conn.commit()
        if previsione == 1:
            model.fit([transazione[:-1]], [previsione])
        time.sleep(1)
        idx += 1

Thread(target=monitor_transactions, args=(model, conn, df_real), daemon=True).start()

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
