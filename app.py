import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle
import plotly.express as px
import os

# Carica il modello pre-addestrato
@st.cache_resource
def load_model():
    if not os.path.exists('model.pkl'):
        st.error("Errore: model.pkl non trovato nel repository!")
        st.stop()
    with open('model.pkl', 'rb') as f:
        model, X_test, y_test = pickle.load(f)
    return model, X_test, y_test

model, X_test, y_test = load_model()

st.title("Guardian - Sicurezza Digitale")
st.write("Rileva frodi in tempo reale con AI")

score = model.score(X_test, y_test)
st.write(f"Accuratezza: {score*100:.2f}%")

st.subheader("Inserisci una transazione")
amount = st.number_input("Importo (€)", min_value=0.0, value=100.0)
v1 = st.number_input("V1", value=0.0)
if st.button("Analizza"):
    nuova_transazione = [[v1] + [0]*(len(X_test.columns)-2) + [amount]]
    previsione = model.predict(nuova_transazione)
    if previsione[0] == 1:
        st.error("ALERT: Frode rilevata!")
    else:
        st.success("Tutto ok, nessuna frode.")

st.subheader("Grafico Frodi")
frodi = y_test.sum()
fig = px.bar(x=["Frodi", "Non Frodi"], y=[frodi, len(y_test)-frodi], 
             title="Distribuzione Frodi", 
             color=["Frodi", "Non Frodi"], 
             color_discrete_map={"Frodi": "#FF5733", "Non Frodi": "#33FF57"})
st.plotly_chart(fig)
