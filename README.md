# Partner Data AI Assistant

Assistente AI conversazionale per interrogare i dati del gestionale OS1.

## Setup Locale

1. Installa dipendenze:
```bash
pip install -r requirements.txt
```

2. Configura `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-xxx
OS1_SERVER=192.168.0.224
OS1_PORT=8090
OS1_USERNAME=PartnerD
OS1_PASSWORD=Partner_2025?
OS1_DBNAME=PartnerD_DB
```

3. Connetti VPN OpenVPN

4. Lancia:
```bash
streamlit run app.py
```

## Deploy su Streamlit Cloud

1. Push su GitHub (SENZA .env!)
2. Vai su https://share.streamlit.io
3. Connetti repo
4. Aggiungi secrets in Settings → Secrets

🚀 ISTRUZIONI DEPLOY
OPZIONE 1: Test Locale (ORA)
bash# 1. Crea cartella e file
mkdir partner-data-ai
cd partner-data-ai

# 2. Crea i file sopra (copia-incolla)

# 3. Installa
pip install -r requirements.txt

# 4. Configura .env con le tue credenziali

# 5. Connetti VPN

# 6. Lancia
streamlit run app.py
