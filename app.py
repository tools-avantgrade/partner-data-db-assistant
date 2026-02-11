python"""
Partner Data AI Assistant
Assistente AI per interrogare i dati del gestionale OS1
"""
import streamlit as st
import anthropic
import json
from api_os1 import OS1Client
from dotenv import load_dotenv
import os

# Carica variabili ambiente
load_dotenv()

# Configurazione pagina
st.set_page_config(
    page_title="Partner Data AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .subtitle {
        color: #666;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Inizializza session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "os1_client" not in st.session_state:
    st.session_state.os1_client = OS1Client()

if "claude_client" not in st.session_state:
    st.session_state.claude_client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

# Tools per Claude (Function Calling)
tools = [
    {
        "name": "get_cliente",
        "description": "Recupera informazioni dettagliate su un cliente specifico dato il suo ID o codice",
        "input_schema": {
            "type": "object",
            "properties": {
                "id_cliente": {
                    "type": "string",
                    "description": "ID o codice del cliente (es. '00001', 'ROSSI01')"
                }
            },
            "required": ["id_cliente"]
        }
    },
    {
        "name": "lista_clienti",
        "description": "Recupera la lista completa di tutti i clienti. Usala per cercare un cliente per nome o per avere un elenco generale.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Numero massimo di clienti da restituire (opzionale, default tutti)"
                }
            }
        }
    },
    {
        "name": "get_ordini_cliente",
        "description": "Recupera gli ordini di un cliente in un periodo specifico",
        "input_schema": {
            "type": "object",
            "properties": {
                "id_cliente": {
                    "type": "string",
                    "description": "ID del cliente"
                },
                "data_da": {
                    "type": "string",
                    "description": "Data inizio periodo formato YYYY-MM-DD (opzionale)"
                },
                "data_a": {
                    "type": "string",
                    "description": "Data fine periodo formato YYYY-MM-DD (opzionale)"
                }
            },
            "required": ["id_cliente"]
        }
    },
    {
        "name": "get_offerte_cliente",
        "description": "Recupera le offerte attive di un cliente",
        "input_schema": {
            "type": "object",
            "properties": {
                "id_cliente": {
                    "type": "string",
                    "description": "ID del cliente (opzionale, se omesso restituisce tutte le offerte)"
                }
            }
        }
    }
]

def process_tool_call(tool_name, tool_input):
    """Esegue la chiamata API richiesta da Claude"""
    os1 = st.session_state.os1_client
    
    if tool_name == "get_cliente":
        return os1.get_cliente(tool_input["id_cliente"])
    
    elif tool_name == "lista_clienti":
        limit = tool_input.get("limit", 50)  # Default 50 per non sovraccaricare
        return os1.lista_clienti(limit=limit)
    
    elif tool_name == "get_ordini_cliente":
        return os1.get_ordini_cliente(
            tool_input["id_cliente"],
            tool_input.get("data_da"),
            tool_input.get("data_a")
        )
    
    elif tool_name == "get_offerte_cliente":
        return os1.get_offerte_cliente(tool_input.get("id_cliente"))
    
    return {"error": f"Tool sconosciuto: {tool_name}"}

def chat_with_ai(user_message):
    """Gestisce la conversazione con Claude"""
    messages = [{"role": "user", "content": user_message}]
    
    with st.spinner("🤔 Sto pensando..."):
        while True:
            response = st.session_state.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                tools=tools,
                messages=messages,
                system="""Sei un assistente AI per Partner Data, un'azienda che usa il gestionale OS1. 
                
Aiuti i commerciali a interrogare i dati aziendali in modo conversazionale.

Quando ti vengono fatte domande su clienti, ordini o offerte:
1. Usa i tool disponibili per recuperare i dati
2. Analizza i dati ricevuti
3. Rispondi in modo chiaro e professionale in italiano
4. Formatta bene le informazioni (usa elenchi, tabelle quando utile)
5. Se i dati sono molti, riassumi i punti salienti

Sii sempre cortese, preciso e orientato al business."""
            )
            
            # Se Claude vuole usare un tool
            if response.stop_reason == "tool_use":
                tool_use = next(block for block in response.content if block.type == "tool_use")
                
                # Mostra quale API sta chiamando (debug)
                with st.expander(f"🔧 API Call: {tool_use.name}", expanded=False):
                    st.json(tool_use.input)
                
                # Esegui il tool
                tool_result = process_tool_call(tool_use.name, tool_use.input)
                
                # Mostra risultato (debug)
                with st.expander(f"📊 Risultato ({len(str(tool_result))} bytes)", expanded=False):
                    if isinstance(tool_result, list):
                        st.write(f"{len(tool_result)} record trovati")
                    st.json(tool_result if len(str(tool_result)) < 5000 else "Troppi dati per visualizzare")
                
                # Aggiungi la risposta di Claude e il risultato del tool
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    }]
                })
            else:
                # Claude ha finito
                text_response = next(
                    (block.text for block in response.content if hasattr(block, "text")),
                    "Scusa, non ho capito."
                )
                return text_response

# ----- INTERFACCIA UTENTE -----

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="title">🤖 Partner Data AI Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Interroga i dati del gestionale con linguaggio naturale</div>', unsafe_allow_html=True)

with col2:
    if st.button("🔄 Nuova Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Sidebar con info e esempi
with st.sidebar:
    st.header("ℹ️ Informazioni")
    
    # Stato connessione
    if st.button("🔌 Test Connessione", use_container_width=True):
        with st.spinner("Test connessione API OS1..."):
            if st.session_state.os1_client.authenticate():
                st.success("✅ Connesso a OS1")
            else:
                st.error("❌ Errore connessione")
    
    st.divider()
    
    st.header("💡 Esempi di domande")
    examples = [
        "Quanti clienti abbiamo?",
        "Dammi info sul cliente 00001",
        "Cerca il cliente Rossi",
        "Ordini del cliente 00001 nel 2026",
        "Quali offerte abbiamo attive?"
    ]
    
    for ex in examples:
        if st.button(f"💬 {ex}", use_container_width=True, key=ex):
            st.session_state.messages.append({"role": "user", "content": ex})
            with st.spinner("Elaborazione..."):
                response = chat_with_ai(ex)
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    st.divider()
    st.caption("🔒 Connesso via VPN a OS1")
    st.caption(f"🗄️ Database: {os.getenv('OS1_DBNAME', 'N/A')}")

# Area chat principale
chat_container = st.container()

with chat_container:
    # Mostra storico conversazione
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Input utente
if prompt := st.chat_input("Fai una domanda sui dati..."):
    # Aggiungi messaggio utente
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Genera risposta AI
    with st.chat_message("assistant"):
        response = chat_with_ai(prompt)
        st.markdown(response)
    
    # Salva risposta
    st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.divider()
st.caption("Demo AI Assistant - Partner Data × AvantGrade")
