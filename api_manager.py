import requests

class APIManager:
    def __init__(self):
        self.currency_url = "https://api.exchangerate-api.com/v4/latest/"

    def get_currency_rates(self):
        try:
            response_usd = requests.get(self.currency_url + "USD")
            data_usd = response_usd.json()
            usd_to_try = data_usd["rates"]["TRY"]

            response_eur = requests.get(self.currency_url + "EUR")
            data_eur = response_eur.json()
            eur_to_try = data_eur["rates"]["TRY"]

            return {
                "USD": usd_to_try,
                "EUR": eur_to_try
            }
        except Exception as e:
            print(f"Döviz çekilirken hata oluştu: {e}")
            return {"USD": "Hata", "EUR": "Hata"}

    def get_weather(self, lat="40.76", lon="29.94"):
        try:
            # Güncel hava durumu, nem, basınç, rüzgar ve hava kodu verilerini çekiyoruz
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,weather_code"
            response = requests.get(weather_url)
            data = response.json()
            
            # Verileri JSON paketinden ayıklıyoruz
            temp = data["current"]["temperature_2m"]
            wind = data["current"]["wind_speed_10m"]
            code = data["current"]["weather_code"] 
            nem = data["current"]["relative_humidity_2m"]
            basinc = data["current"]["surface_pressure"]
            rakim = data.get("elevation", "---") # YENİ: Rakım (Elevation) verisini çekiyoruz
            
            return {
                "temperature": temp,
                "windspeed": wind,
                "weathercode": code,
                "humidity": nem,
                "pressure": basinc,
                "elevation": rakim # YENİ: Arayüze gönderiyoruz
            }
        except Exception as e:
            print(f"Hava durumu çekilirken hata oluştu: {e}")
            return {"temperature": "Hata", "windspeed": "Hata", "weathercode": -1, "humidity": "Hata", "pressure": "Hata", "elevation": "Hata"}