"""
Partner Data AI Assistant
Chatbot conversazionale per interrogare il gestionale OS1 in linguaggio naturale.

Uso: streamlit run app.py
Requisiti: VPN attiva, API key Anthropic configurata
"""

import streamlit as st
import anthropic
import json
import os
from datetime import datetime
from api_os1 import OS1Client

# ──────────────────────────────────────────────
# CONFIGURAZIONE
# ──────────────────────────────────────────────

# Inserisci la tua API key Anthropic qui o in variabile d'ambiente
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "sk-ant-api03-INSERISCI-LA-TUA-KEY")

SYSTEM_PROMPT = """Sei l'assistente AI di Partner Data, un'azienda italiana che vende soluzioni 
di identificazione automatica (smart card, lettori, stampanti card, tecnologia RFID, controllo accessi).

Il tuo ruolo è aiutare i commerciali a trovare rapidamente informazioni su clienti, ordini, offerte, 
fatture e vendite dal gestionale OS1.

COME COMPORTARTI:
- Rispondi SEMPRE in italiano
- Sii conciso e professionale, vai dritto al punto
- Quando l'utente menziona un cliente, prima cercalo per nome o codice
- Per domande su fatturato, recupera le fatture e calcola i totali
- Formatta gli importi in euro (€) con separatore migliaia (es: €127.350,00)
- Formatta le date in formato italiano (gg/mm/aaaa)
- Se i dati non bastano per rispondere, chiedi chiarimenti
- Se un tool non restituisce risultati, dillo chiaramente
- Puoi fare più chiamate API in sequenza se necessario (es: prima cerca cliente, poi prendi le fatture)

STATI DEI DOCUMENTI:
- Offerte e ordini hanno 3 stati possibili: "inevaso", "evaso totalmente", "evaso parzialmente"
- "Offerte aperte" = offerte con stato "inevaso"
- "Offerte chiuse" = offerte con stato "evaso totalmente"

CATEGORIE PRODOTTO (da arricchire con file Excel di Francesco):
- Gruppi vendita (macro): reparto card, reparto animali, reparto smart card, hardware, lettori
- Categorie merceologiche (dettaglio): tessera combo, tessera contatto, tessera RFID, ecc.

CLIENTE DI TEST: codice 444 = MS., storico dal 2015 ad oggi.

Oggi è il {today}.
""".format(today=datetime.now().strftime("%d/%m/%Y"))

# ──────────────────────────────────────────────
# DEFINIZIONE TOOLS PER CLAUDE
# ──────────────────────────────────────────────

TOOLS = [
    {
        "name": "cerca_cliente",
        "description": (
            "Cerca un cliente nel database OS1 per nome, ragione sociale o codice numerico. "
            "Usa questo tool quando l'utente menziona un cliente specifico e vuoi trovare "
            "il suo codice o le sue informazioni anagrafiche. Restituisce una lista di clienti trovati."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Nome, ragione sociale o codice numerico del cliente da cercare"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_dettaglio_cliente",
        "description": (
            "Recupera i dettagli anagrafici completi di un cliente dato il suo codice numerico. "
            "Usa questo quando hai già il codice cliente e vuoi i dati completi (indirizzo, contatti, ecc.)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "id_cliente": {
                    "type": "string",
                    "description": "Codice numerico del cliente (es: '444')"
                }
            },
            "required": ["id_cliente"]
        }
    },
    {
        "name": "get_offerte_cliente",
        "description": (
            "Recupera le offerte/preventivi di un cliente dal gestionale OS1. "
            "Usa questo quando l'utente chiede: offerte aperte, preventivi, prezzi offerti, "
            "offerte da sollecitare, stato delle offerte. "
            "Puoi filtrare per periodo con data_da e data_a."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "id_cliente": {
                    "type": "string",
                    "description": "Codice numerico del cliente"
                },
                "data_da": {
                    "type": "string",
                    "description": "Data inizio periodo, formato YYYY-MM-DD (opzionale)"
                },
                "data_a": {
                    "type": "string",
                    "description": "Data fine periodo, formato YYYY-MM-DD (opzionale)"
                }
            },
            "required": ["id_cliente"]
        }
    },
    {
        "name": "get_ordini_cliente",
        "description": (
            "Recupera gli ordini di un cliente dal gestionale OS1. "
            "Usa questo quando l'utente chiede: ordini, stato ordini, date consegna, "
            "ordini evasi o inevasi, storico ordini. "
            "Puoi filtrare per periodo e per agente commerciale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "id_cliente": {
                    "type": "string",
                    "description": "Codice numerico del cliente"
                },
                "data_da": {
                    "type": "string",
                    "description": "Data inizio periodo, formato YYYY-MM-DD (opzionale)"
                },
                "data_a": {
                    "type": "string",
                    "description": "Data fine periodo, formato YYYY-MM-DD (opzionale)"
                },
                "id_agente": {
                    "type": "string",
                    "description": "Codice agente commerciale (opzionale)"
                }
            },
            "required": ["id_cliente"]
        }
    },
    {
        "name": "get_fatture_cliente",
        "description": (
            "Recupera le fatture e note di credito di un cliente dal gestionale OS1. "
            "Usa questo quando l'utente chiede: fatturato, fatture, importi, "
            "analisi economica, quanto ha speso un cliente, volume d'affari. "
            "Per calcolare il fatturato totale, somma gli importi delle fatture nel periodo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "id_cliente": {
                    "type": "string",
                    "description": "Codice numerico del cliente"
                },
                "data_da": {
                    "type": "string",
                    "description": "Data inizio periodo, formato YYYY-MM-DD (opzionale)"
                },
                "data_a": {
                    "type": "string",
                    "description": "Data fine periodo, formato YYYY-MM-DD (opzionale)"
                }
            },
            "required": ["id_cliente"]
        }
    },
    {
        "name": "get_bolle_cliente",
        "description": (
            "Recupera i DDT (documenti di trasporto / bolle) di un cliente. "
            "Usa questo quando l'utente chiede: consegne, spedizioni, date di consegna, DDT."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "id_cliente": {
                    "type": "string",
                    "description": "Codice numerico del cliente"
                },
                "data_da": {
                    "type": "string",
                    "description": "Data inizio periodo, formato YYYY-MM-DD (opzionale)"
                },
                "data_a": {
                    "type": "string",
                    "description": "Data fine periodo, formato YYYY-MM-DD (opzionale)"
                }
            },
            "required": ["id_cliente"]
        }
    },
    {
        "name": "lista_clienti",
        "description": (
            "Recupera la lista di tutti i clienti nel database. "
            "Usa solo se l'utente chiede esplicitamente di vedere tutti i clienti o una lista generale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Numero massimo di clienti da restituire (default: 20)",
                    "default": 20
                }
            },
            "required": []
        }
    }
]

# ──────────────────────────────────────────────
# ESECUZIONE TOOLS
# ──────────────────────────────────────────────

def execute_tool(os1_client, tool_name, tool_input):
    """Esegue il tool richiesto da Claude e restituisce il risultato."""
    try:
        if tool_name == "cerca_cliente":
            result = os1_client.cerca_cliente(tool_input["query"])
        elif tool_name == "get_dettaglio_cliente":
            result = os1_client.get_cliente(tool_input["id_cliente"])
        elif tool_name == "get_offerte_cliente":
            result = os1_client.get_offerte_cliente(
                id_cliente=tool_input["id_cliente"],
                data_da=tool_input.get("data_da"),
                data_a=tool_input.get("data_a")
            )
        elif tool_name == "get_ordini_cliente":
            result = os1_client.get_ordini_cliente(
                id_cliente=tool_input["id_cliente"],
                data_da=tool_input.get("data_da"),
                data_a=tool_input.get("data_a"),
                id_agente=tool_input.get("id_agente")
            )
        elif tool_name == "get_fatture_cliente":
            result = os1_client.get_fatture_cliente(
                id_cliente=tool_input["id_cliente"],
                data_da=tool_input.get("data_da"),
                data_a=tool_input.get("data_a")
            )
        elif tool_name == "get_bolle_cliente":
            result = os1_client.get_bolle_cliente(
                id_cliente=tool_input["id_cliente"],
                data_da=tool_input.get("data_da"),
                data_a=tool_input.get("data_a")
            )
        elif tool_name == "lista_clienti":
            result = os1_client.lista_clienti(
                limit=tool_input.get("limit", 20)
            )
        else:
            result = {"error": f"Tool sconosciuto: {tool_name}"}

        # Tronca risultati troppo grandi per non superare il contesto di Claude
        result_json = json.dumps(result, ensure_ascii=False, default=str)
        if len(result_json) > 50000:
            if isinstance(result, list):
                result = result[:30]  # Limita a 30 record
                result.append({"_nota": f"Risultati troncati. Totale originale: {len(result)} record."})
            result_json = json.dumps(result, ensure_ascii=False, default=str)

        return result_json

    except ConnectionError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Errore durante {tool_name}: {str(e)}"})


# ──────────────────────────────────────────────
# CHAT CON CLAUDE + FUNCTION CALLING LOOP
# ──────────────────────────────────────────────

def chat_with_claude(client, os1_client, messages):
    """
    Invia messaggi a Claude con tools. Gestisce il loop di function calling:
    Claude può fare più chiamate API prima di dare la risposta finale.
    """
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=messages
    )

    # Loop: Claude potrebbe voler fare più chiamate API
    max_iterations = 10  # Sicurezza anti-loop infinito
    iteration = 0

    while response.stop_reason == "tool_use" and iteration < max_iterations:
        iteration += 1

        # Aggiungi la risposta di Claude (con tool_use) alla conversazione
        messages.append({"role": "assistant", "content": response.content})

        # Esegui TUTTI i tool richiesti (Claude può chiederne più di uno)
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                # Mostra nell'interfaccia quale API sta chiamando
                st.caption(f"🔍 Chiamo `{block.name}` con parametri: {json.dumps(block.input, ensure_ascii=False)}")

                result = execute_tool(os1_client, block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

        # Rimanda i risultati a Claude
        messages.append({"role": "user", "content": tool_results})

        # Claude elabora i risultati e decide: risponde o fa altre chiamate
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

    # Estrai la risposta testuale finale
    text_parts = []
    for block in response.content:
        if hasattr(block, "text"):
            text_parts.append(block.text)

    final_text = "\n".join(text_parts) if text_parts else "Non sono riuscito a elaborare una risposta."

    # Aggiungi risposta finale alla conversazione
    messages.append({"role": "assistant", "content": response.content})

    return final_text


# ──────────────────────────────────────────────
# INTERFACCIA STREAMLIT
# ──────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Partner Data AI Assistant",
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 Partner Data AI Assistant")
    st.caption("Interroga il gestionale OS1 in linguaggio naturale")

    # ── Sidebar: configurazione e stato ──
    with st.sidebar:
        st.header("⚙️ Configurazione")

        api_key = st.text_input(
            "Anthropic API Key",
            value=ANTHROPIC_API_KEY if "INSERISCI" not in ANTHROPIC_API_KEY else "",
            type="password",
            help="Inserisci la tua API key Anthropic"
        )

        st.divider()
        st.header("📡 Stato Connessione")

        # Test connessione OS1
        if st.button("🔌 Testa connessione OS1"):
            with st.spinner("Connessione in corso..."):
                os1 = OS1Client()
                result = os1.test_connection()
                if result["status"] == "ok":
                    st.success(result["message"])
                else:
                    st.error(result["message"])

        st.divider()
        st.header("💡 Domande di esempio")
        st.markdown("""
        - *Dammi info sul cliente 444*
        - *Che offerte aperte ha il cliente MS.?*
        - *Fatturato del cliente 444 nel 2024*
        - *Ordini del cliente 444 negli ultimi 6 mesi*
        - *Ci sono offerte da sollecitare per il cliente 444?*
        - *Mostrami le ultime fatture del cliente 444*
        """)

        st.divider()
        if st.button("🗑️ Pulisci chat"):
            st.session_state.messages = []
            st.session_state.api_messages = []
            st.rerun()

    # ── Inizializzazione stato sessione ──
    if "messages" not in st.session_state:
        st.session_state.messages = []  # Per visualizzazione UI
    if "api_messages" not in st.session_state:
        st.session_state.api_messages = []  # Per API Claude (include tool calls)

    # ── Mostra storico chat ──
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Input utente ──
    if prompt := st.chat_input("Scrivi la tua domanda sui dati Partner Data..."):
        # Verifica API key
        if not api_key or "INSERISCI" in api_key:
            st.error("⚠️ Inserisci la tua Anthropic API Key nella sidebar.")
            return

        # Mostra messaggio utente
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Chiama Claude
        with st.chat_message("assistant"):
            with st.spinner("Sto cercando i dati..."):
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    os1_client = OS1Client()

                    # Aggiungi messaggio utente alla conversazione API
                    st.session_state.api_messages.append({
                        "role": "user",
                        "content": prompt
                    })

                    # Chat con function calling loop
                    response_text = chat_with_claude(
                        client,
                        os1_client,
                        st.session_state.api_messages
                    )

                    st.markdown(response_text)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text
                    })

                except anthropic.AuthenticationError:
                    st.error("❌ API Key Anthropic non valida. Controlla nella sidebar.")
                except ConnectionError as e:
                    st.error(f"❌ {str(e)}")
                except Exception as e:
                    st.error(f"❌ Errore: {str(e)}")


if __name__ == "__main__":
    main()
