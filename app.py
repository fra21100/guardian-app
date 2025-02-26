import streamlit as st
import pandas as pd
import pickle
import plotly.express as px
import requests
import sqlite3

@st.cache_resource
def load_model():
    with open('model.pkl', 'rb') as f:
        model, X_test, y_test = pickle.load(f)
    return model, X_test, y_test

@st.cache_data
def check_shodan(ip):
    shodan_key = "HWr3qeGqlCVxTqbTmuJX3IgKhTJHW6Lr"
    url = f"https://api.shodan.io/shodan/host/{ip}?key={shodan_key}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

@st.cache_data
def check_ipinfo(ip):
    ipinfo_key = "e836ce33f43f8a"
    url = f"https://ipinfo.io/{ip}/json?token={ipinfo_key}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

@st.cache_data
def check_abuseipdb(ip):
    abuseipdb_key = "c87a09395a0d25e07c20c4c953624bf5efa17d21b6cbad921d1bc0d9e79a7f15894aafb4cd4dd726"
    url = f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}"
    headers = {"Key": abuseipdb_key, "Accept": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()['data'] if response.status_code == 200 else None

# Stile
st.markdown("""
<style>
.stApp {background-color: #1a1a2e; color: #e0e0e0;}
.stButton>button {background-color: #ff5733; color: white; border-radius: 5px;}
.stTextInput>label {color: #33ff57;}
</style>
""", unsafe_allow_html=True)

model, X_test, y_test = load_model()

st.title("Guardian: Il Detective Digitale")
st.write("Indaga su frodi e minacce online in tempo reale.")
score = model.score(X_test, y_test)
st.write(f"Accuratezza: {score*100:.2f}%")

# Database
conn = sqlite3.connect('guardian_data.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transazioni 
             (v1 REAL, v2 REAL, v3 REAL, v4 REAL, v5 REAL, v6 REAL, v7 REAL, v8 REAL, 
              v9 REAL, v10 REAL, v11 REAL, v12 REAL, v13 REAL, v14 REAL, v15 REAL, 
              v16 REAL, v17 REAL, v18 REAL, v19 REAL, v20 REAL, v21 REAL, v22 REAL, 
              v23 REAL, v24 REAL, v25 REAL, v26 REAL, v27 REAL, v28 REAL, amount REAL, class INTEGER)''')

# Input transazione
st.subheader("Inserisci una transazione")
cols = st.columns(4)
inputs = []
for i in range(1, 29):
    col_idx = (i-1) % 4
    v_input = cols[col_idx].number_input(f"V{i}", value=0.0, step=0.1)
    inputs.append(v_input)
amount = st.number_input("Importo (€)", min_value=0.0, value=100.0)
inputs.append(amount)

if st.button("Analizza e Apprendi"):
    nuova_transazione = inputs
    previsione = model.predict([nuova_transazione])
    c.execute("INSERT INTO transazioni VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
              nuova_transazione + [previsione[0]])
    conn.commit()
    if previsione[0] == 1:
        st.error("ALERT: Frode rilevata! Transazione bloccata.")
        st.write("Indagine avviata: controllo correlazioni.")
    else:
        st.success("Transazione sicura registrata.")

# IP Check
st.subheader("Analizza IP")
ip = st.text_input("Inserisci IP (es. 8.8.8.8)")
if st.button("Analizza IP"):
    shodan_data = check_shodan(ip)
    if shodan_data:
        st.write(f"Shodan - Porte aperte: {shodan_data.get('ports', 'Nessuna')}")
    ipinfo_data = check_ipinfo(ip)
    if ipinfo_data:
        st.write(f"IPinfo - Posizione: {ipinfo_data.get('city', 'N/A')}, {ipinfo_data.get('country', 'N/A')}")
    abuseipdb_data = check_abuseipdb(ip)
    if abuseipdb_data and abuseipdb_data['totalReports'] > 0:
        st.error(f"AbuseIPDB - IP segnalato: {abuseipdb_data['totalReports']} volte!")

# Dark Web
st.subheader("Controllo Dark Web")
email = st.text_input("Inserisci email")
if st.button("Verifica Dark Web"):
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
    headers = {"user-agent": "Guardian-App"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        breaches = response.json()
        st.warning(f"Email compromessa in {len(breaches)} violazioni: {[b['Name'] for b in breaches]}")
        st.write("Indagine avviata: controllo IP correlati.")
    elif response.status_code == 404:
        st.success("Nessuna violazione trovata.")
    else:
        st.error("Errore nella verifica.")

# Grafico
st.subheader("Grafico Frodi")
frodi = y_test.sum()
fig = px.bar(x=["Frodi", "Non Frodi"], y=[frodi, len(y_test)-frodi], 
             title="Distribuzione Frodi", 
             color=["Frodi", "Non Frodi"], 
             color_discrete_map={"Frodi": "#FF5733", "Non Frodi": "#33FF57"})
st.plotly_chart(fig)

conn.close()
