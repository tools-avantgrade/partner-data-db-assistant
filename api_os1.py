"""
Client API per OS1 ERP - Partner Data
Gestisce autenticazione JWT e chiamate REST al gestionale.
Requisito: connessione VPN attiva verso 192.168.0.224
"""

import requests
import time
import logging

logger = logging.getLogger(__name__)


class OS1Client:
    def __init__(self, server="192.168.0.224", port=8090):
        self.base_url = f"http://{server}:{port}/rest/idea"
        self.token = None
        self.token_time = None
        # Credenziali hard-coded per evitare problemi con carattere ? in password
        self.credentials = {
            "username": "PartnerD",
            "password": "Partner_2025?",
            "dbname": "PartnerD"
        }

    def authenticate(self):
        """Ottieni JWT token da OS1. Rinnova se scaduto."""
        try:
            response = requests.post(
                f"{self.base_url}/token",
                data=self.credentials,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get("IsVerified"):
                self.token = data["Token"]
                self.token_time = time.time()
                logger.info("Autenticazione OS1 riuscita")
                return True
            else:
                logger.error(f"Autenticazione fallita: {data}")
                return False

        except requests.exceptions.ConnectionError:
            logger.error("Impossibile connettersi a OS1. Verifica che la VPN sia attiva.")
            raise ConnectionError(
                "Connessione a OS1 fallita. Assicurati che la VPN OpenVPN sia attiva "
                "e che il server 192.168.0.224 sia raggiungibile."
            )
        except Exception as e:
            logger.error(f"Errore autenticazione: {e}")
            raise

    def _get_headers(self):
        """Restituisce headers con token JWT. Rinnova se necessario."""
        # Rinnova token ogni 25 minuti (margine di sicurezza)
        if not self.token or (time.time() - (self.token_time or 0)) > 1500:
            self.authenticate()
        return {"Authorization": f"Bearer {self.token}"}

    def _get(self, endpoint, params=None):
        """Chiamata GET generica con gestione errori."""
        # Rimuovi parametri None
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                # Token scaduto, riprova
                self.token = None
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=self._get_headers(),
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
            raise
        except Exception as e:
            logger.error(f"Errore chiamata {endpoint}: {e}")
            raise

    # ──────────────────────────────────────────────
    # CLIENTI
    # ──────────────────────────────────────────────

    def cerca_cliente(self, query):
        """Cerca cliente per codice, nome o ragione sociale."""
        # Prova prima per codice esatto
        if query.isdigit():
            try:
                result = self._get(f"/erp/cliente/{query}")
                if result:
                    return result if isinstance(result, list) else [result]
            except Exception as e:
                logger.warning(f"Ricerca diretta per codice '{query}' fallita: {e}, provo ricerca generica")

        # Ricerca generica su lista clienti
        clienti = self._get("/erp/cliente")
        if not clienti:
            return []

        query_lower = query.lower()
        trovati = []
        for c in clienti:
            searchable = " ".join(str(v) for v in c.values() if v).lower()
            if query_lower in searchable:
                trovati.append(c)

        return trovati[:20]  # Max 20 risultati

    def get_cliente(self, id_cliente):
        """Dettaglio singolo cliente per codice."""
        try:
            return self._get(f"/erp/cliente/{id_cliente}")
        except Exception as e:
            logger.warning(f"Dettaglio cliente '{id_cliente}' fallito: {e}")
            return {"error": f"Cliente con codice '{id_cliente}' non trovato o errore API: {str(e)}"}

    def lista_clienti(self, limit=50):
        """Lista clienti (primi N)."""
        clienti = self._get("/erp/cliente")
        if isinstance(clienti, list):
            return clienti[:limit]
        return clienti

    # ──────────────────────────────────────────────
    # OFFERTE CLIENTI
    # ──────────────────────────────────────────────

    def get_offerte_cliente(self, id_cliente=None, data_da=None, data_a=None):
        """
        Recupera offerte/preventivi.
        Filtri: idcliente, dadata (YYYY-MM-DD), adata (YYYY-MM-DD)
        """
        params = {}
        if id_cliente:
            params["idcliente"] = id_cliente
        if data_da:
            params["dadata"] = data_da
        if data_a:
            params["adata"] = data_a

        return self._get("/erp/offerteclienti", params)

    # ──────────────────────────────────────────────
    # ORDINI CLIENTI
    # ──────────────────────────────────────────────

    def get_ordini_cliente(self, id_cliente=None, data_da=None, data_a=None, id_agente=None):
        """
        Recupera ordini cliente.
        Filtri: idcliente, dadata, adata, idagente
        """
        params = {}
        if id_cliente:
            params["idcliente"] = id_cliente
        if data_da:
            params["dadata"] = data_da
        if data_a:
            params["adata"] = data_a
        if id_agente:
            params["idagente"] = id_agente

        return self._get("/erp/ordiniclienti", params)

    # ──────────────────────────────────────────────
    # FATTURE CLIENTI
    # ──────────────────────────────────────────────

    def get_fatture_cliente(self, id_cliente=None, data_da=None, data_a=None):
        """
        Recupera fatture e note credito.
        Filtri: idcliente, dadata, adata
        """
        params = {}
        if id_cliente:
            params["idcliente"] = id_cliente
        if data_da:
            params["dadata"] = data_da
        if data_a:
            params["adata"] = data_a

        return self._get("/erp/fattureclienti", params)

    # ──────────────────────────────────────────────
    # DDT / BOLLE CLIENTI
    # ──────────────────────────────────────────────

    def get_bolle_cliente(self, id_cliente=None, data_da=None, data_a=None):
        """
        Recupera DDT (documenti di trasporto).
        Filtri: idcliente, dadata, adata
        """
        params = {}
        if id_cliente:
            params["idcliente"] = id_cliente
        if data_da:
            params["dadata"] = data_da
        if data_a:
            params["adata"] = data_a

        return self._get("/erp/bolleclienti", params)

    # ──────────────────────────────────────────────
    # TEST CONNESSIONE
    # ──────────────────────────────────────────────

    def test_connection(self):
        """Verifica che VPN e autenticazione funzionino."""
        try:
            success = self.authenticate()
            if success:
                # Prova una chiamata reale
                clienti = self._get("/erp/cliente")
                n = len(clienti) if isinstance(clienti, list) else 0
                return {
                    "status": "ok",
                    "message": f"Connessione OK. {n} clienti trovati nel database.",
                    "token_preview": self.token[:20] + "..." if self.token else None
                }
            return {"status": "error", "message": "Autenticazione fallita (IsVerified: false)"}
        except ConnectionError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Errore: {str(e)}"}
