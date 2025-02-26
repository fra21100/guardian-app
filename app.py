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

model, X_test, y_test = load_model()

st.title("Guardian - Sicurezza Digitale")
st.write("Rileva frodi, IP sospetti e dispositivi vulnerabili con AI")

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

# Shodan API
st.subheader("Cerca Dispositivi con Shodan")
ip_shodan = st.text_input("Inserisci IP per Shodan (es. 8.8.8.8)")
if st.button("Cerca con Shodan"):
    api_key = "HWr3qeGqlCVxTqbTmuJX3IgKhTJHW6Lr"  # Sostituisci con la tua chiave Shodan
    url = f"https://api.shodan.io/shodan/host/{ip_shodan}?key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        st.write(f"Porte aperte: {data.get('ports', 'Nessuna')}")
        st.write(f"Dettagli: {data.get('data', 'N/A')}")
    else:
        st.error(f"Errore nella ricerca: {response.status_code}")

# IPinfo API
st.subheader("Geolocalizza IP")
ip_info = st.text_input("Inserisci IP per IPinfo (es. 8.8.8.8)")
if st.button("Geolocalizza"):
    api_key = "e836ce33f43f8a"  # Sostituisci con la tua chiave IPinfo
    url = f"https://ipinfo.io/{ip_info}/json?token={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        st.write(f"Posizione: {data.get('city', 'N/A')}, {data.get('country', 'N/A')}")
        st.write(f"ISP: {data.get('org', 'N/A')}")
    else:
        st.error(f"Errore nella geolocalizzazione: {response.status_code}")

# AbuseIPDB API
st.subheader("Controlla IP su AbuseIPDB")
ip_abuse = st.text_input("Inserisci IP per AbuseIPDB (es. 8.8.8.8)")
if st.button("Controlla IP"):
    api_key = "c87a09395a0d25e07c20c4c953624bf5efa17d21b6cbad921d1bc0d9e79a7f15894aafb4cd4dd726"  # Sostituisci con la tua chiave AbuseIPDB
    url = f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip_abuse}"
    headers = {"Key": api_key, "Accept": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()['data']
        st.write(f"Segnalazioni: {data['totalReports']}")
        if data['isWhitelisted']:
            st.success("IP sicuro.")
        elif data['totalReports'] > 0:
            st.error("IP segnalato come pericoloso!")
        else:
            st.success("Nessuna segnalazione.")
    else:
        st.error(f"Errore nella verifica: {response.status_code}")

# Grafico
st.subheader("Grafico Frodi")
frodi = y_test.sum()
fig = px.bar(x=["Frodi", "Non Frodi"], y=[frodi, len(y_test)-frodi], 
             title="Distribuzione Frodi", 
             color=["Frodi", "Non Frodi"], 
             color_discrete_map={"Frodi": "#FF5733", "Non Frodi": "#33FF57"})
st.plotly_chart(fig)
