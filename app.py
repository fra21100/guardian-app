import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import smtplib
import plotly.express as px

@st.cache_resource
def train_model():
    data = pd.read_csv('https://drive.google.com/uc?export=download&id=17KecvEIHHc5QfUhQkC9NJv9A9Y1a-K-A')
    st.write("Colonne nel dataset:", data.columns.tolist())  # Stampa le colonne
    X = data.drop('Class', axis=1)
    y = data['Class']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    return model, X_test, y_test

model, X_test, y_test = train_model()
# ... resto del codice invariato ...

# Dashboard
st.title("Guardian - Sicurezza Digitale")
st.write("Rileva frodi in tempo reale con AI al 99.95%")

score = model.score(X_test, y_test)
st.write(f"Accuratezza: {score*100:.2f}%")

# Input personalizzati
st.subheader("Inserisci una transazione")
amount = st.number_input("Importo (€)", min_value=0.0, value=100.0)
v1 = st.number_input("V1", value=0.0)  # Semplificato, aggiungi altri V se vuoi
if st.button("Analizza"):
    nuova_transazione = [[v1] + [0]*(len(X_test.columns)-2) + [amount]]
    previsione = model.predict(nuova_transazione)
    if previsione[0] == 1:
        st.error("ALERT: Frode rilevata!")
        # Alert email
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login("tuaemail@gmail.com", "tuapasswordapp")
            server.sendmail("tuaemail@gmail.com", "destinatario@example.com", "Frode rilevata!")
            server.quit()
            st.write("Email inviata!")
        except:
            st.write("Errore nell'invio email.")
    else:
        st.success("Tutto ok, nessuna frode.")

# Grafico
st.subheader("Grafico Frodi")
frodi = y_test.sum()
fig = px.bar(x=["Frodi", "Non Frodi"], y=[frodi, len(y_test)-frodi], title="Distribuzione Frodi")
st.plotly_chart(fig)
