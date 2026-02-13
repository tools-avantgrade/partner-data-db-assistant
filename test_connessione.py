# Partner Data AI Assistant

Chatbot conversazionale per interrogare il gestionale OS1 in linguaggio naturale.

## Setup rapido

```bash
# 1. Installa dipendenze
pip install -r requirements.txt

# 2. Connetti la VPN OpenVPN verso Partner Data

# 3. Inserisci la tua Anthropic API key in app.py (riga 19) oppure:
export ANTHROPIC_API_KEY=sk-ant-api03-...

# 4. Testa la connessione
python test_connessione.py

# 5. Lancia l'app
streamlit run app.py
```

## Struttura

- `app.py` — Interfaccia Streamlit + Claude function calling loop
- `api_os1.py` — Client API OS1 (autenticazione JWT + chiamate REST)
- `test_connessione.py` — Script test rapido connessione

## Note

- Richiede VPN attiva per accedere a 192.168.0.224:8090
- Le credenziali OS1 sono hard-coded in api_os1.py (password con carattere speciale ?)
- Cliente di test: codice 444 (MS.), storico dal 2015
