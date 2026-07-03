import requests
import random
import time
import os

class ERPConnector:
    def cadastrar_item_mro(self, item_data):
        raise NotImplementedError("Método não implementado")

class MockERPConnector(ERPConnector):
    def cadastrar_item_mro(self, item_data):
        time.sleep(0.5)
        if random.random() > 0.2:
            return {"sucesso": True, "mensagem": "Cadastrado com sucesso", "codigo_erp": f"ERP-{random.randint(1000,9999)}"}
        else:
            return {"sucesso": False, "mensagem": "Erro: Part Number duplicado ou inválido", "codigo_erp": None}

class SAPConnector(ERPConnector):
    def __init__(self):
        self.url = os.getenv("SAP_URL")
        self.auth = (os.getenv("SAP_USER"), os.getenv("SAP_PASS"))

    def cadastrar_item_mro(self, item_data):
        payload = {
            "MaterialType": "HIBE",
            "MaterialDesc": item_data.get('Description'),
            "ManufProfId": item_data.get('Manufacturer'),
            "BaseUnit": "UN",
            "Price": str(item_data.get('Price'))
        }
        try:
            response = requests.post(f"{self.url}/API_MATERIAL_SRV/A_Material", 
                                     json=payload, auth=self.auth, timeout=10)
            if response.status_code == 201:
                return {"sucesso": True, "mensagem": "Criado no SAP", "codigo_erp": response.json().get('d', {}).get('Material')}
            return {"sucesso": False, "mensagem": f"SAP Error {response.status_code}: {response.text}", "codigo_erp": None}
        except Exception as e:
            return {"sucesso": False, "mensagem": str(e), "codigo_erp": None}

class TOTVSConnector(ERPConnector):
    def __init__(self):
        self.url = os.getenv("TOTVS_URL")
        self.headers = {"Authorization": f"Bearer {os.getenv('TOTVS_TOKEN')}", "Content-Type": "application/json"}

    def cadastrar_item_mro(self, item_data):
        payload = {
            "B1_COD": item_data.get('Part Number'),
            "B1_DESC": item_data.get('Description'),
            "B1_UM": "UN",
            "B1_PRV1": item_data.get('Price')
        }
        try:
            response = requests.post(f"{self.url}/api/data/SB1", json=payload, headers=self.headers, timeout=10)
            if response.status_code in [200, 201]:
                return {"sucesso": True, "mensagem": "Criado no TOTVS", "codigo_erp": item_data.get('Part Number')}
            return {"sucesso": False, "mensagem": f"TOTVS Error: {response.text}", "codigo_erp": None}
        except Exception as e:
            return {"sucesso": False, "mensagem": str(e), "codigo_erp": None}
