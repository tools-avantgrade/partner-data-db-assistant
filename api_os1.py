import requests
import os
from datetime import datetime, timedelta
import streamlit as st

class OS1Client:
    def __init__(self):
        self.server = os.getenv("OS1_SERVER", "192.168.0.224")
        self.port = os.getenv("OS1_PORT", "8090")
        self.base_url = f"http://{self.server}:{self.port}/rest/idea"
        self.token = None
        self.token_expiry = None
        
    def authenticate(self):
        """Autentica e ottiene token"""
        url = f"{self.base_url}/token"
        data = {
            "username": os.getenv("OS1_USERNAME"),
            "password": os.getenv("OS1_PASSWORD"),
            "dbname": os.getenv("OS1_DBNAME")
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("IsVerified"):
                self.token = result["Token"]
                # Parse expiration (ISO format)
                exp_str = result.get("Expiration", "")
                if exp_str:
                    self.token_expiry = datetime.fromisoformat(exp_str.replace("+01:00", ""))
                return True
            return False
        except Exception as e:
            st.error(f"Errore autenticazione: {e}")
            return False
    
    def ensure_authenticated(self):
        """Verifica che il token sia valido, altrimenti ri-autentica"""
        if not self.token or not self.token_expiry:
            return self.authenticate()
        
        # Se il token scade tra meno di 5 minuti, rinnova
        if datetime.now() > (self.token_expiry - timedelta(minutes=5)):
            return self.authenticate()
        
        return True
    
    def _get_headers(self):
        """Ritorna headers con token"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def get_cliente(self, id_cliente):
        """Recupera informazioni su un cliente specifico"""
        if not self.ensure_authenticated():
            return {"error": "Autenticazione fallita"}
        
        url = f"{self.base_url}/erp/cliente/{id_cliente}"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def lista_clienti(self, limit=None):
        """Recupera lista clienti"""
        if not self.ensure_authenticated():
            return {"error": "Autenticazione fallita"}
        
        url = f"{self.base_url}/erp/cliente"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if limit and isinstance(data, list):
                return data[:limit]
            return data
        except Exception as e:
            return {"error": str(e)}
    
    def get_ordini_cliente(self, id_cliente, data_da=None, data_a=None):
        """Recupera ordini di un cliente"""
        if not self.ensure_authenticated():
            return {"error": "Autenticazione fallita"}
        
        url = f"{self.base_url}/erp/ordiniclienti"
        params = {"idcliente": id_cliente}
        
        if data_da:
            params["dadata"] = data_da
        if data_a:
            params["adata"] = data_a
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_offerte_cliente(self, id_cliente=None):
        """Recupera offerte cliente"""
        if not self.ensure_authenticated():
            return {"error": "Autenticazione fallita"}
        
        url = f"{self.base_url}/erp/offerteclienti"
        params = {}
        
        if id_cliente:
            params["idcliente"] = id_cliente
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
