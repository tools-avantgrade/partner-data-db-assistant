"""
Test rapido connessione API OS1.
Eseguilo PRIMA di lanciare l'app Streamlit per verificare che VPN e credenziali funzionino.

Uso: python test_connessione.py
"""

from api_os1 import OS1Client
import json

def main():
    print("=" * 60)
    print("TEST CONNESSIONE API OS1 - Partner Data")
    print("=" * 60)

    os1 = OS1Client()

    # 1. Test autenticazione
    print("\n1️⃣  Test autenticazione...")
    result = os1.test_connection()
    if result["status"] == "ok":
        print(f"   ✅ {result['message']}")
    else:
        print(f"   ❌ {result['message']}")
        print("\n   Verifica che:")
        print("   - La VPN OpenVPN sia attiva")
        print("   - Il server 192.168.0.224 sia raggiungibile")
        print("   - Le credenziali siano corrette")
        return

    # 2. Test cliente 444 (MS.)
    print("\n2️⃣  Test ricerca cliente 444 (MS.)...")
    cliente = os1.get_cliente("444")
    if cliente:
        print(f"   ✅ Cliente trovato:")
        print(f"   {json.dumps(cliente, indent=2, ensure_ascii=False)[:500]}")
    else:
        print("   ⚠️  Cliente 444 non trovato")

    # 3. Test offerte cliente 444
    print("\n3️⃣  Test offerte cliente 444...")
    offerte = os1.get_offerte_cliente(id_cliente="444")
    if isinstance(offerte, list):
        print(f"   ✅ Trovate {len(offerte)} offerte")
        if offerte:
            print(f"   Prima offerta: {json.dumps(offerte[0], indent=2, ensure_ascii=False)[:300]}")
    else:
        print(f"   Risultato: {json.dumps(offerte, ensure_ascii=False)[:300]}")

    # 4. Test ordini cliente 444
    print("\n4️⃣  Test ordini cliente 444...")
    ordini = os1.get_ordini_cliente(id_cliente="444")
    if isinstance(ordini, list):
        print(f"   ✅ Trovati {len(ordini)} ordini")
    else:
        print(f"   Risultato: {json.dumps(ordini, ensure_ascii=False)[:300]}")

    # 5. Test fatture cliente 444
    print("\n5️⃣  Test fatture cliente 444...")
    fatture = os1.get_fatture_cliente(id_cliente="444")
    if isinstance(fatture, list):
        print(f"   ✅ Trovate {len(fatture)} fatture")
    else:
        print(f"   Risultato: {json.dumps(fatture, ensure_ascii=False)[:300]}")

    print("\n" + "=" * 60)
    print("Test completati! Se tutto è ✅, puoi lanciare l'app:")
    print("  streamlit run app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
