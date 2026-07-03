import requests
import os

class WhatsAppNotifier:
    def enviar_relatorio(self, telefone, mensagem):
        raise NotImplementedError("Método não implementado")

class MockWhatsAppNotifier(WhatsAppNotifier):
    def enviar_relatorio(self, telefone, mensagem):
        with open("log_whatsapp_mock.txt", "a", encoding="utf-8") as f:
            f.write(f"Para: {telefone}\n{mensagem}\n{'-'*50}\n")
        return True

class TwilioWhatsAppNotifier(WhatsAppNotifier):
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_SID")
        self.auth_token = os.getenv("TWILIO_TOKEN")
        self.twilio_phone = os.getenv("TWILIO_PHONE")
        self.url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

    def enviar_relatorio(self, telefone, mensagem):
        payload = {
            "From": f"whatsapp:{self.twilio_phone}",
            "To": f"whatsapp:{telefone}",
            "Body": mensagem
        }
        try:
            response = requests.post(self.url, data=payload, auth=(self.account_sid, self.auth_token), timeout=15)
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Erro WhatsApp: {e}")
            return False
