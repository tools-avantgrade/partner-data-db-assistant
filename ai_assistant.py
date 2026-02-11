import anthropic
import requests
import json

# Configurazione
VPN_SERVER = "192.168.0.224:8090"
API_BASE = f"http://{VPN_SERVER}/rest/idea"

# Token ottenuto dall'autenticazione
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJSb2xlcyI6InN0YW5kYXJkLGFkbWluIiwiZHVyYXRpb24iOiIxODk5LTEyLTMxIiwiREJOQU1FIjoiUGFydG5lckRfREIiLCJpc3MiOiJNQVJTLUN1cmlvc2l0eSIsImV4cCI6MTc3MDg5MTQzMiwiaWF0IjoxNzcwODA1MDMyLCJVc2VyTmFtZSI6IlBhcnRuZXJEIn0.H_ITVVoxFOe_zAlJVM8Ka2NS9P3kVdJtT6HCyvoEY_o"

# Funzioni che chiamano le API OS1
def get_cliente(id_cliente):
    """Recupera informazioni su un cliente"""
    url = f"{API_BASE}/erp/cliente/{id_cliente}"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.json()

def get_ordini_cliente(id_cliente, data_da=None, data_a=None):
    """Recupera ordini di un cliente"""
    url = f"{API_BASE}/erp/ordiniclienti"
    params = {"idcliente": id_cliente}
    if data_da:
        params["dadata"] = data_da
    if data_a:
        params["adata"] = data_a
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def lista_clienti():
    """Recupera lista di tutti i clienti"""
    url = f"{API_BASE}/erp/cliente"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.json()

# Tools per Claude
tools = [
    {
        "name": "get_cliente",
        "description": "Recupera informazioni dettagliate su un cliente specifico dato il suo ID",
        "input_schema": {
            "type": "object",
            "properties": {
                "id_cliente": {
                    "type": "string",
                    "description": "ID del cliente (es. '00001')"
                }
            },
            "required": ["id_cliente"]
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
                    "description": "Data inizio periodo (YYYY-MM-DD), opzionale"
                },
                "data_a": {
                    "type": "string",
                    "description": "Data fine periodo (YYYY-MM-DD), opzionale"
                }
            },
            "required": ["id_cliente"]
        }
    },
    {
        "name": "lista_clienti",
        "description": "Recupera la lista completa di tutti i clienti",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    }
]

# Client Anthropic
client = anthropic.Anthropic(api_key="LA_TUA_API_KEY")

def process_tool_call(tool_name, tool_input):
    """Esegue la funzione richiesta da Claude"""
    if tool_name == "get_cliente":
        return get_cliente(tool_input["id_cliente"])
    elif tool_name == "get_ordini_cliente":
        return get_ordini_cliente(
            tool_input["id_cliente"],
            tool_input.get("data_da"),
            tool_input.get("data_a")
        )
    elif tool_name == "lista_clienti":
        return lista_clienti()

def chat(user_message):
    """Gestisce una conversazione con l'AI"""
    messages = [{"role": "user", "content": user_message}]
    
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            tools=tools,
            messages=messages
        )
        
        # Se Claude vuole usare un tool
        if response.stop_reason == "tool_use":
            # Trova il tool call
            tool_use = next(block for block in response.content if block.type == "tool_use")
            
            print(f"🔧 Claude chiama: {tool_use.name}({tool_use.input})")
            
            # Esegui il tool
            tool_result = process_tool_call(tool_use.name, tool_use.input)
            
            print(f"📊 Risultato: {len(str(tool_result))} caratteri di dati")
            
            # Aggiungi la risposta di Claude e il risultato del tool
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(tool_result)
                }]
            })
        else:
            # Claude ha finito, ritorna la risposta
            text_response = next(
                (block.text for block in response.content if hasattr(block, "text")),
                None
            )
            return text_response

# Test
if __name__ == "__main__":
    print("🤖 Assistente AI Partner Data")
    print("=" * 50)
    
    while True:
        domanda = input("\n👤 Tu: ")
        if domanda.lower() in ["exit", "quit"]:
            break
            
        risposta = chat(domanda)
        print(f"\n🤖 AI: {risposta}")
