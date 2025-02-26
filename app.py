import streamlit as st
import pandas as pd
import pickle
import plotly.express as px
import requests

@st.cache_resource
def load_model():
    with open('model.pkl', 'rb') as f:
        model, X_test, y_test = pickle.load(f)
    return model, X_test, y_test

# Funzioni API con caching
@st.cache_data
def check_shodan(ip):
    shodan_key = "HWr3qeGqlCVxTqbTmuJX3IgKhTJHW6Lr"  # Sostituisci con la tua
    url = f"https://api.shodan.io/shodan/host/{ip}?key={shodan_key}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

@st.cache_data
def check_ipinfo(ip):
    ipinfo_key = "e836ce33f43f8a"  # Sostituisci con la tua
    url = f"https://ipinfo.io/{ip}/json?token={ipinfo_key}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

@st.cache_data
def check_abuseipdb(ip):
    abuseipdb_key = "c87a09395a0d25e07c20c4c953624bf5efa17d21b6cbad921d1bc0d9e79a7f15894aafb4cd4dd726"  # Sostituisci con la tua
    url = f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}"
    headers = {"Key": abuseipdb_key, "Accept": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()['data'] if response.status_code == 200 else None

# Main app
model, X_test, y_test = load_model()

st.title("Guardian - Sicurezza Digitale")
st.write("Benvenuto in Guardian! Analizza transazioni sospette o verifica la sicurezza di un IP.")
score = model.score(X_test, y_test)
st.write(f"Accuratezza: {score*100:.2f}%")

# Input transazione
st.subheader("Inserisci una transazione")
amount = st.number_input("Importo (€)", min_value=0.0, value=100.0)
v1 = st.number_input("V1", value=0.0)
if st.button("Analizza Transazione"):
    nuova_transazione = [[v1] + [0]*(len(X_test.columns)-2) + [amount]]
    previsione = model.predict(nuova_transazione)
    if previsione[0] == 1:
        st.error("ALERT: Frode rilevata!")
    else:
        st.success("Tutto ok, nessuna frode.")

# Unificato IP Check con caching
st.subheader("Analizza IP")
ip = st.text_input("Inserisci IP (es. 8.8.8.8)")
if st.button("Analizza IP"):
    # Shodan
    shodan_data = check_shodan(ip)
    if shodan_data:
        st.write(f"Shodan - Porte aperte: {shodan_data.get('ports', 'Nessuna')}")
    else:
        st.write("Shodan - Errore nella ricerca o dati non disponibili.")

    # IPinfo
    ipinfo_data = check_ipinfo(ip)
    if ipinfo_data:
        st.write(f"IPinfo - Posizione: {ipinfo_data.get('city', 'N/A')}, {ipinfo_data.get('country', 'N/A')}")
        st.write(f"IPinfo - ISP: {ipinfo_data.get('org', 'N/A')}")
    else:
        st.write("IPinfo - Errore nella geolocalizzazione.")

    # AbuseIPDB
    abuseipdb_data = check_abuseipdb(ip)
    if abuseipdb_data:
        st.write(f"AbuseIPDB - Segnalazioni: {abuseipdb_data['totalReports']}")
        if abuseipdb_data['isWhitelisted']:
            st.success("AbuseIPDB - IP sicuro.")
        elif abuseipdb_data['totalReports'] > 0:
            st.error("AbuseIPDB - IP segnalato come pericoloso!")
        else:
            st.success("AbuseIPDB - Nessuna segnalazione.")
    else:
        st.write("AbuseIPDB - Errore nella verifica.")

# Grafico
st.subheader("Grafico Frodi")
frodi = y_test.sum()
fig = px.bar(x=["Frodi", "Non Frodi"], y=[frodi, len(y_test)-frodi], 
             title="Distribuzione Frodi", 
             color=["Frodi", "Non Frodi"], 
             color_discrete_map={"Frodi": "#FF5733", "Non Frodi": "#33FF57"})
st.plotly_chart(fig)
