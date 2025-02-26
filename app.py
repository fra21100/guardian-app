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
st.write("Rileva frodi, minacce dark web e URL sospetti con AI")

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

# VirusTotal URL Scan
st.subheader("Analizza URL Sospetto")
url = st.text_input("Inserisci URL (es. http://example.com)")
if st.button("Scansiona URL"):
    api_key = "1234abcd5678efgh9012ijkl3456mnop"  # Sostituisci con la tua chiave
    vt_url = "https://www.virustotal.com/api/v3/urls"
    headers = {"x-apikey": api_key}
    # Codifica l'URL per l'analisi
    payload = {"url": url}
    response = requests.post(vt_url, headers=headers, data=payload)
    if response.status_code == 200:
        scan_id = response.json()['data']['id']
        # Recupera i risultati
        analysis_url = f"https://www.virustotal.com/api/v3/analyses/{scan_id}"
        analysis_response = requests.get(analysis_url, headers=headers)
        if analysis_response.status_code == 200:
            result = analysis_response.json()['data']['attributes']['stats']
            st.write(f"Risultati scansione: Malicious: {result['malicious']}, Suspicious: {result['suspicious']}, Clean: {result['harmless']}")
            if result['malicious'] > 0 or result['suspicious'] > 0:
                st.error("ATTENZIONE: URL potenzialmente pericoloso!")
            else:
                st.success("URL sicuro.")
        else:
            st.error("Errore nell'analisi dei risultati.")
    else:
        st.error(f"Errore nella richiesta: {response.status_code}")

# Grafico
st.subheader("Grafico Frodi")
frodi = y_test.sum()
fig = px.bar(x=["Frodi", "Non Frodi"], y=[frodi, len(y_test)-frodi], 
             title="Distribuzione Frodi", 
             color=["Frodi", "Non Frodi"], 
             color_discrete_map={"Frodi": "#FF5733", "Non Frodi": "#33FF57"})
st.plotly_chart(fig)
