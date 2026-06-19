import customtkinter as ctk
import math
import datetime
import threading
import os
import sys # YENİ: Dosya konumlarını sabitlemek için eklendi
from api_manager import APIManager

# --- DOSYA KONUMLARINI SABİTLEME (PROGRAM NEREDEYSE DOSYALAR ORADA OLUŞUR) ---
if getattr(sys, 'frozen', False):
    # Eğer program .exe yapılmışsa .exe'nin olduğu klasörü bul
    KLASOR = os.path.dirname(sys.executable)
else:
    # Eğer program .py olarak çalışıyorsa .py'nin olduğu klasörü bul
    KLASOR = os.path.dirname(os.path.abspath(__file__))

NOT_DOSYASI = os.path.join(KLASOR, "saha_notlari.txt")
GECMIS_TXT = os.path.join(KLASOR, "gecmis.txt")
GECMIS_CSV = os.path.join(KLASOR, "Hesaplama_Raporu.csv")


# --- GENEL AYARLAR ---
ctk.set_appearance_mode("dark") 
ctk.set_default_color_theme("blue") 
G = 9.80665 

bolge_koordinatlari = {
    "Kocaeli": {"Merkez (İzmit)": ("40.76", "29.94"), "Gebze": ("40.80", "29.43"), "Gölcük": ("40.71", "29.82")},
    "İstanbul": {"Merkez": ("41.01", "28.97"), "Kadıköy": ("40.99", "29.02"), "Beşiktaş": ("41.04", "29.00")},
    "Ankara": {"Merkez": ("39.92", "32.85"), "Çankaya": ("39.89", "32.86")},
    "İzmir": {"Merkez": ("38.42", "27.14"), "Karşıyaka": ("38.45", "27.11")},
    "Dünya (Ekstrem)": {"Catatumbo (Venezuela)": ("9.34", "-71.72"), "Mawsynram (Hindistan)": ("25.30", "91.58"), "McMurdo (Antarktika)": ("-77.84", "166.68")}
}

hava_ikonlari = {
    0: "☀️ Açık", 1: "🌤️ Çoğunlukla Açık", 2: "⛅ Parçalı Bulutlu", 3: "☁️ Çok Bulutlu",
    45: "🌫️ Sisli", 48: "🌫️ Yoğun Sisli", 51: "🌧️ Hafif Çisenti", 53: "🌧️ Orta Çisenti",
    55: "🌧️ Yoğun Çisenti", 61: "🌧️ Hafif Yağmurlu", 63: "🌧️ Orta Yağmurlu", 65: "🌧️ Şiddetli Yağmurlu",
    71: "❄️ Hafif Kar Yağışlı", 73: "❄️ Orta Kar Yağışlı", 75: "❄️ Yoğun Kar Yağışlı",
    95: "⛈️ Fırtınalı", 96: "⛈️ Şiddetli Fırtına"
}

hava_renkleri = {
    0: "#FFD700", 1: "#FFD700", 2: "#FFFFFF", 3: "#FFFFFF", 45: "#CCCCCC", 48: "#CCCCCC",
    51: "#4FC3F7", 53: "#4FC3F7", 55: "#4FC3F7", 61: "#4FC3F7", 63: "#4FC3F7", 65: "#4FC3F7",
    71: "#E0F7FA", 73: "#E0F7FA", 75: "#E0F7FA", 95: "#B39DDB", 96: "#B39DDB"
}

muhendislik_sabitleri = {
    "Yerçekimi İvmesi (g)": "9.80665 m/s²",
    "Pi Sayısı (π)": "3.14159265...",
    "Suyun Yoğunluğu (4°C)": "1000 kg/m³",
    "Çeliğin Yoğunluğu": "7850 kg/m³",
    "Standart Atmosfer Basıncı": "101325 Pa (1.013 bar)",
    "Işık Hızı (c)": "299,792,458 m/s",
    "İdeal Gaz Sabiti (R)": "8.31446 J/(mol·K)"
}

sabitler_penceresi = None
gecmis_penceresi = None

# --- FONKSİYONLAR ---

def sabitleri_goster():
    global sabitler_penceresi
    if sabitler_penceresi is not None and sabitler_penceresi.winfo_exists():
        sabitler_penceresi.focus()
        return

    sabitler_penceresi = ctk.CTkToplevel(app)
    sabitler_penceresi.title("Referans Sabitler")
    sabitler_penceresi.geometry("400x450")
    sabitler_penceresi.attributes("-topmost", True)
    
    baslik = ctk.CTkLabel(sabitler_penceresi, text="Mühendislik Sabitleri", font=("Arial", 18, "bold"), text_color="#3a7ebf")
    baslik.pack(pady=15)
    
    kutu = ctk.CTkTextbox(sabitler_penceresi, font=("Arial", 14))
    kutu.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    for ad, deger in muhendislik_sabitleri.items():
        kutu.insert("end", f"📌 {ad}:\n{deger}\n\n")
    kutu.configure(state="disabled")

def gecmisi_temizle(metin_kutusu, bilgi_etiketi):
    try:
        with open(GECMIS_TXT, "w", encoding="utf-8") as dosya:
            pass
            
        if os.path.exists(GECMIS_CSV):
            with open(GECMIS_CSV, "w", encoding="utf-8-sig") as csv_dosya:
                csv_dosya.write("Tarih/Saat;İslem Türü;Hesaplama\n")
                
        metin_kutusu.configure(state="normal")
        metin_kutusu.delete("1.0", "end") 
        metin_kutusu.insert("1.0", "Geçmiş başarıyla temizlendi.") 
        metin_kutusu.configure(state="disabled")
        
        bilgi_etiketi.configure(text="Geçmiş Silindi! 🗑️", text_color="#dc3545")
        app.after(3000, lambda: bilgi_etiketi.configure(text=""))
    except Exception as e:
        bilgi_etiketi.configure(text="Silme Hatası!", text_color="#FF6666")

def gecmisi_excel_yap(bilgi_etiketi):
    try:
        with open(GECMIS_TXT, "r", encoding="utf-8") as txt_dosya:
            satirlar = txt_dosya.readlines()
            
        with open(GECMIS_CSV, "w", encoding="utf-8-sig") as csv_dosya:
            csv_dosya.write("Tarih/Saat;İslem Türü;Hesaplama\n")
            for satir in satirlar:
                if "]" in satir and "|" in satir:
                    zaman = satir.split("]")[0].replace("[", "").strip()
                    islem = satir.split("]")[1].split("|")[0].strip()
                    hesap = satir.split("|")[1].strip()
                    csv_dosya.write(f"{zaman};{islem};{hesap}\n")
                    
        bilgi_etiketi.configure(text="Excel Raporu Yeniden Oluşturuldu! ✔️", text_color="#28a745")
        app.after(3000, lambda: bilgi_etiketi.configure(text=""))
    except Exception as e:
        bilgi_etiketi.configure(text="Kayıt Yok veya Hata!", text_color="#FF6666")

def gecmisi_goster():
    global gecmis_penceresi
    if gecmis_penceresi is not None and gecmis_penceresi.winfo_exists():
        gecmis_penceresi.focus()
        return

    gecmis_penceresi = ctk.CTkToplevel(app)
    gecmis_penceresi.title("Hesaplama Geçmişi")
    gecmis_penceresi.geometry("600x450")
    gecmis_penceresi.attributes("-topmost", True) 
    
    baslik = ctk.CTkLabel(gecmis_penceresi, text="Son İşlemler", font=("Arial", 18, "bold"), text_color="#3a7ebf")
    baslik.pack(pady=10)
    
    alt_kutu = ctk.CTkFrame(gecmis_penceresi, fg_color="transparent")
    alt_kutu.pack(side="bottom", fill="x", pady=(0, 10))
    
    csv_bilgi = ctk.CTkLabel(alt_kutu, text="", font=("Arial", 12, "bold"))
    csv_bilgi.pack(side="bottom", pady=(5, 0))
    
    buton_kutusu = ctk.CTkFrame(alt_kutu, fg_color="transparent")
    buton_kutusu.pack(side="bottom")
    
    temizle_btn = ctk.CTkButton(buton_kutusu, text="🗑️ Temizle", font=("Arial", 14, "bold"), fg_color="#dc3545", hover_color="#c82333", width=120, command=lambda: gecmisi_temizle(metin_kutusu, csv_bilgi))
    temizle_btn.pack(side="left", padx=10)
    
    csv_btn = ctk.CTkButton(buton_kutusu, text="📥 Excel'e Aktar (.csv)", font=("Arial", 14, "bold"), fg_color="#28a745", hover_color="#218838", command=lambda: gecmisi_excel_yap(csv_bilgi))
    csv_btn.pack(side="left", padx=10)

    metin_kutusu = ctk.CTkTextbox(gecmis_penceresi, font=("Arial", 14))
    metin_kutusu.pack(fill="both", expand=True, padx=20, pady=(0, 10))
    
    try:
        with open(GECMIS_TXT, "r", encoding="utf-8") as dosya:
            gecmis_verisi = dosya.read()
            if gecmis_verisi.strip() == "": 
                metin_kutusu.insert("1.0", "Henüz bir hesaplama yapılmadı.") 
            else: 
                metin_kutusu.insert("1.0", gecmis_verisi) 
    except FileNotFoundError:
        metin_kutusu.insert("1.0", "Henüz bir hesaplama yapılmadı.") 
        
    metin_kutusu.configure(state="disabled")

def sonucu_kopyala():
    metin = sonuc_etiketi.cget("text")
    if "---" not in metin and "Hata" not in metin:
        temiz_sonuc = metin.replace("Sonuç: ", "")
        app.clipboard_clear()
        app.clipboard_append(temiz_sonuc)
        kopyala_butonu.configure(text="Kopyalandı! ✔️", fg_color="#28a745")
        app.after(2000, lambda: kopyala_butonu.configure(text="Sonucu Kopyala", fg_color=["#3B8ED0", "#1F6AA5"]))

def hesapla(event=None):
    try:
        deger_metni = giris_kutusu.get().replace(',', '.')
        deger = float(deger_metni)
        secim = menu.get()
        sonuc = 0
        birim = ""

        if secim == "m -> cm": sonuc = deger * 100; birim = "cm"
        elif secim == "cm -> m": sonuc = deger / 100; birim = "m"
        elif secim == "cm -> mm": sonuc = deger * 10; birim = "mm"
        elif secim == "mm -> cm": sonuc = deger / 10; birim = "cm"
        elif secim == "Celsius -> Fahrenheit": sonuc = (deger * 1.8) + 32; birim = "°F"
        elif secim == "Fahrenheit -> Celsius": sonuc = (deger - 32) / 1.8; birim = "°C"
        elif secim == "Bar -> PSI": sonuc = deger * 14.5038; birim = "PSI"
        elif secim == "PSI -> Bar": sonuc = deger / 14.5038; birim = "Bar"
        elif secim == "HP -> kW": sonuc = deger * 0.7457; birim = "kW"
        elif secim == "kW -> HP": sonuc = deger / 0.7457; birim = "HP"
        elif secim == "Serbest Düşme Hızı (m -> m/s)": sonuc = math.sqrt(2 * G * deger); birim = "m/s"
        elif secim == "Serbest Düşme Yük. (m/s -> m)": sonuc = (deger ** 2) / (2 * G); birim = "m"
        elif secim == "Ağırlık Hesabı (kg -> Newton)": sonuc = deger * G; birim = "N"
        elif secim == "Kütle Hesabı (Newton -> kg)": sonuc = deger / G; birim = "kg"
        elif secim == "m/s -> km/h": sonuc = deger * 3.6; birim = "km/h"
        elif secim == "km/h -> m/s": sonuc = deger / 3.6; birim = "m/s"
        elif secim == "Joule -> Kalori": sonuc = deger / 4.184; birim = "cal"
        elif secim == "Kalori -> Joule": sonuc = deger * 4.184; birim = "J"

        son_metin = f"{sonuc:.3f} {birim}"
        sonuc_etiketi.configure(text=f"Sonuç: {son_metin}", text_color="#FFFFFF")
        
        zaman = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
        
        try:
            kayit_metni = f"[{zaman}] {secim} | Girilen: {deger} -> Bulunan: {son_metin}\n"
            with open(GECMIS_TXT, "a", encoding="utf-8") as dosya:
                dosya.write(kayit_metni)
                
            dosya_var_mi = os.path.exists(GECMIS_CSV)
            with open(GECMIS_CSV, "a", encoding="utf-8-sig") as csv_dosya:
                if not dosya_var_mi:
                    csv_dosya.write("Tarih/Saat;İslem Türü;Hesaplama\n")
                csv_dosya.write(f"{zaman};{secim};{deger} -> {son_metin}\n")
                
        except Exception as e:
            print("Kayıt hatası:", e)

    except ValueError:
        sonuc_etiketi.configure(text="Hata: Geçerli bir sayı girin!", text_color="#FF6666")

def yon_degistir():
    mevcut_secim = menu.get()
    ters_yonler = {
        "m -> cm": "cm -> m", "cm -> m": "m -> cm",
        "cm -> mm": "mm -> cm", "mm -> cm": "cm -> mm",
        "Celsius -> Fahrenheit": "Fahrenheit -> Celsius", "Fahrenheit -> Celsius": "Celsius -> Fahrenheit",
        "Bar -> PSI": "PSI -> Bar", "PSI -> Bar": "Bar -> PSI",
        "HP -> kW": "kW -> HP", "kW -> HP": "HP -> kW",
        "Ağırlık Hesabı (kg -> Newton)": "Kütle Hesabı (Newton -> kg)", "Kütle Hesabı (Newton -> kg)": "Ağırlık Hesabı (kg -> Newton)",
        "m/s -> km/h": "km/h -> m/s", "km/h -> m/s": "m/s -> km/h",
        "Joule -> Kalori": "Kalori -> Joule", "Kalori -> Joule": "Joule -> Kalori",
        "Serbest Düşme Hızı (m -> m/s)": "Serbest Düşme Yük. (m/s -> m)", "Serbest Düşme Yük. (m/s -> m)": "Serbest Düşme Hızı (m -> m/s)"
    }
    yeni_secim = ters_yonler.get(mevcut_secim, mevcut_secim)
    menu.set(yeni_secim)
    if giris_kutusu.get() != "": hesapla()

def notlari_kaydet():
    try:
        # Metni okuyup gereksiz boşlukları (strip) kesiyoruz
        kaydedilecek_not = notlar_kutusu.get("1.0", "end-1c").strip()
        
        with open(NOT_DOSYASI, "w", encoding="utf-8") as f:
            f.write(kaydedilecek_not)
            
        notlar_kaydet_btn.configure(text="✔️", fg_color="#28a745")
        app.after(2000, lambda: notlar_kaydet_btn.configure(text="💾", fg_color="transparent"))
        
    except PermissionError:
        # YENİ: Dosya Windows tarafından kilitlenmişse (açıksa) bu blok çalışır
        print("Hata: Dosya açık olduğu için kilitli.")
        notlar_kaydet_btn.configure(text="KİLİTLİ!", fg_color="#ffc107", text_color="#000000") # Sarı uyarı
        app.after(2500, lambda: notlar_kaydet_btn.configure(text="💾", fg_color="transparent", text_color="#FFFFFF"))
        
    except Exception as e:
        # Diğer beklenmedik hatalar için
        print(f"Not kaydetme hatası: {e}")
        notlar_kaydet_btn.configure(text="HATA", fg_color="#dc3545")
        app.after(2000, lambda: notlar_kaydet_btn.configure(text="💾", fg_color="transparent"))

# --- ARAYÜZ ---
app = ctk.CTk()
app.title("Mühendislik Saha Asistanı v2.0")
app.geometry("1000x700") 
app.minsize(900, 650)
app.after(0, lambda: app.state('zoomed')) 

sol_panel = ctk.CTkFrame(app, fg_color="transparent")
sol_panel.pack(side="left", fill="both", expand=True, padx=20, pady=20)

sag_panel = ctk.CTkFrame(app, width=330, fg_color="#1e1e1e", corner_radius=15) 
sag_panel.pack(side="right", fill="y", padx=20, pady=20)
sag_panel.pack_propagate(False)

ana_icerik = ctk.CTkFrame(sol_panel, fg_color="transparent")
ana_icerik.place(relx=0.5, rely=0.5, anchor="center")

baslik = ctk.CTkLabel(ana_icerik, text="Mühendislik Hesaplama Modülü", font=("Arial", 28, "bold"))
baslik.pack(pady=(0, 30))

giris_kutusu = ctk.CTkEntry(ana_icerik, placeholder_text="Hesaplanacak değeri girin...", width=380, height=50, font=("Arial", 16))
giris_kutusu.pack(pady=15)
giris_kutusu.focus()

menu_cerceve = ctk.CTkFrame(ana_icerik, fg_color="transparent")
menu_cerceve.pack(pady=15)

degistir_butonu = ctk.CTkButton(menu_cerceve, text="⇄", width=50, height=50, font=("Arial", 22, "bold"), command=yon_degistir)
degistir_butonu.pack(side="left", padx=(0, 15))

menu = ctk.CTkOptionMenu(menu_cerceve, values=[
    "m -> cm", "cm -> mm", 
    "Celsius -> Fahrenheit", "Bar -> PSI", "HP -> kW",
    "Serbest Düşme Hızı (m -> m/s)", "Ağırlık Hesabı (kg -> Newton)", 
    "m/s -> km/h", "Joule -> Kalori"
], width=315, height=50, font=("Arial", 16), dropdown_font=("Arial", 14))
menu.pack(side="left")

sonuc_etiketi = ctk.CTkLabel(ana_icerik, text="Sonuç: ---", font=("Arial", 24, "bold"))
sonuc_etiketi.pack(pady=(35, 10))

kopyala_butonu = ctk.CTkButton(ana_icerik, text="Sonucu Kopyala", command=sonucu_kopyala, width=120, height=35, font=("Arial", 14))
kopyala_butonu.pack(pady=(0, 30))

hesapla_butonu = ctk.CTkButton(ana_icerik, text="HESAPLA", command=hesapla, width=220, height=55, font=("Arial", 18, "bold"))
hesapla_butonu.pack(pady=10)

alt_butonlar_kutu = ctk.CTkFrame(ana_icerik, fg_color="transparent")
alt_butonlar_kutu.pack(pady=(15, 0))

sabitler_butonu = ctk.CTkButton(alt_butonlar_kutu, text="📐 Sabitler", command=sabitleri_goster, width=140, height=40, font=("Arial", 14), fg_color="#17a2b8", hover_color="#138496")
sabitler_butonu.pack(side="left", padx=5)

gecmis_butonu = ctk.CTkButton(alt_butonlar_kutu, text="🕒 Geçmiş Kayıtlar", command=gecmisi_goster, width=140, height=40, font=("Arial", 14), fg_color="#444444", hover_color="#555555")
gecmis_butonu.pack(side="left", padx=5)

# --- SAĞ PANEL ---
sag_baslik = ctk.CTkLabel(sag_panel, text="ANLIK SAHA VERİLERİ", font=("Arial", 20, "bold"), text_color="#3a7ebf")
sag_baslik.pack(pady=(20, 10))

doviz_cerceve = ctk.CTkFrame(sag_panel, fg_color="#2b2b2b")
doviz_cerceve.pack(fill="x", padx=15, pady=5, ipady=5)

doviz_ust_kutu = ctk.CTkFrame(doviz_cerceve, fg_color="transparent")
doviz_ust_kutu.pack(fill="x", padx=10, pady=(5, 5))
doviz_etiket = ctk.CTkLabel(doviz_ust_kutu, text="Döviz Kurları", font=("Arial", 16, "bold"))
doviz_etiket.pack(side="left")
doviz_yenile_btn = ctk.CTkButton(doviz_ust_kutu, text="🔄", width=30, height=30, font=("Arial", 16), fg_color="transparent", hover_color="#444444")
doviz_yenile_btn.pack(side="right")

usd_bilgi = ctk.CTkLabel(doviz_cerceve, text="USD/TRY: Yükleniyor...", font=("Arial", 14))
usd_bilgi.pack(pady=2)
eur_bilgi = ctk.CTkLabel(doviz_cerceve, text="EUR/TRY: Yükleniyor...", font=("Arial", 14))
eur_bilgi.pack(pady=(2, 5))

hava_cerceve = ctk.CTkFrame(sag_panel, fg_color="#2b2b2b")
hava_cerceve.pack(fill="x", padx=15, pady=5, ipady=5)

hava_ust_kutu = ctk.CTkFrame(hava_cerceve, fg_color="transparent")
hava_ust_kutu.pack(fill="x", padx=10, pady=(5, 5))
hava_etiket = ctk.CTkLabel(hava_ust_kutu, text="Hava Durumu", font=("Arial", 16, "bold"))
hava_etiket.pack(side="left")
hava_yenile_btn = ctk.CTkButton(hava_ust_kutu, text="🔄", width=30, height=30, font=("Arial", 16), fg_color="transparent", hover_color="#444444")
hava_yenile_btn.pack(side="right")

sehir_menu = ctk.CTkOptionMenu(hava_cerceve, values=list(bolge_koordinatlari.keys()), width=180, height=30)
sehir_menu.pack(pady=4)
sehir_menu.set("Kocaeli") 

ilce_menu = ctk.CTkOptionMenu(hava_cerceve, values=list(bolge_koordinatlari["Kocaeli"].keys()), width=180, height=30)
ilce_menu.pack(pady=4)
ilce_menu.set("Merkez (İzmit)")

durum_bilgi = ctk.CTkLabel(hava_cerceve, text="Durum: Yükleniyor...", font=("Arial", 16, "bold"), text_color="#FFFFFF")
durum_bilgi.pack(pady=(5, 5))

sicaklik_bilgi = ctk.CTkLabel(hava_cerceve, text="Sıcaklık: -- °C", font=("Arial", 14))
sicaklik_bilgi.pack(pady=1)
nem_bilgi = ctk.CTkLabel(hava_cerceve, text="Bağıl Nem: -- %", font=("Arial", 14))
nem_bilgi.pack(pady=1)
basinc_bilgi = ctk.CTkLabel(hava_cerceve, text="Basınç: -- hPa", font=("Arial", 14))
basinc_bilgi.pack(pady=1)
ruzgar_bilgi = ctk.CTkLabel(hava_cerceve, text="Rüzgar: -- km/h", font=("Arial", 14))
ruzgar_bilgi.pack(pady=1)

rakim_bilgi = ctk.CTkLabel(hava_cerceve, text="Rakım: -- m", font=("Arial", 14))
rakim_bilgi.pack(pady=(1, 5))

notlar_cerceve = ctk.CTkFrame(sag_panel, fg_color="#2b2b2b")
notlar_cerceve.pack(fill="both", expand=True, padx=15, pady=10) 

notlar_ust_kutu = ctk.CTkFrame(notlar_cerceve, fg_color="transparent")
notlar_ust_kutu.pack(fill="x", padx=10, pady=(10, 5))
notlar_etiket = ctk.CTkLabel(notlar_ust_kutu, text="Saha Notları", font=("Arial", 16, "bold"))
notlar_etiket.pack(side="left")

notlar_kaydet_btn = ctk.CTkButton(notlar_ust_kutu, text="💾", width=30, height=30, font=("Arial", 16), fg_color="transparent", hover_color="#444444", command=notlari_kaydet)
notlar_kaydet_btn.pack(side="right")

notlar_kutusu = ctk.CTkTextbox(notlar_cerceve, font=("Arial", 14), wrap="word")
notlar_kutusu.pack(fill="both", expand=True, padx=10, pady=(0, 10))

try:
    with open(NOT_DOSYASI, "r", encoding="utf-8") as f:
        notlar_kutusu.insert("1.0", f.read())
except FileNotFoundError:
    pass

# --- API THREADING ---
def bagimsiz_doviz_guncelle():
    doviz_yenile_btn.configure(text="⏳", fg_color="#3B8ED0")
    def arka_planda_cek():
        kurlar = APIManager().get_currency_rates()
        app.after(0, doviz_arayuzunu_guncelle, kurlar)
    threading.Thread(target=arka_planda_cek, daemon=True).start()

def doviz_arayuzunu_guncelle(kurlar):
    if kurlar["USD"] != "Hata":
        usd_bilgi.configure(text=f"USD/TRY: {kurlar['USD']:.4f} ₺", text_color="#FFFFFF")
        eur_bilgi.configure(text=f"EUR/TRY: {kurlar['EUR']:.4f} ₺", text_color="#FFFFFF")
    else:
        usd_bilgi.configure(text="USD/TRY: Bağlantı Hatası", text_color="#FF6666")
        eur_bilgi.configure(text="EUR/TRY: Bağlantı Hatası", text_color="#FF6666")
    doviz_yenile_btn.configure(text="🔄", fg_color="transparent")

def bagimsiz_hava_guncelle(event=None):
    hava_yenile_btn.configure(text="⏳", fg_color="#3B8ED0")
    secilen_sehir = sehir_menu.get()
    secilen_ilce = ilce_menu.get()
    def arka_planda_cek():
        lat, lon = bolge_koordinatlari[secilen_sehir][secilen_ilce]
        hava = APIManager().get_weather(lat, lon)
        app.after(0, hava_arayuzunu_guncelle, hava)
    threading.Thread(target=arka_planda_cek, daemon=True).start()

def hava_arayuzunu_guncelle(hava):
    if hava["temperature"] != "Hata":
        sicaklik_bilgi.configure(text=f"Sıcaklık: {hava['temperature']} °C", text_color="#FFFFFF")
        nem_bilgi.configure(text=f"Bağıl Nem: %{hava['humidity']}", text_color="#FFFFFF")
        basinc_bilgi.configure(text=f"Basınç: {hava['pressure']} hPa", text_color="#FFFFFF")
        ruzgar_bilgi.configure(text=f"Rüzgar: {hava['windspeed']} km/h", text_color="#FFFFFF")
        rakim_bilgi.configure(text=f"Rakım: {hava['elevation']} m", text_color="#FFFFFF") 
        
        durum_metni = hava_ikonlari.get(hava["weathercode"], "☁️ Bilinmeyen Durum")
        durum_rengi = hava_renkleri.get(hava["weathercode"], "#FFFFFF")
        durum_bilgi.configure(text=durum_metni, text_color=durum_rengi)
    else:
        sicaklik_bilgi.configure(text="Sıcaklık: Bağlantı Hatası", text_color="#FF6666")
        nem_bilgi.configure(text="Bağıl Nem: Bağlantı Hatası", text_color="#FF6666")
        basinc_bilgi.configure(text="Basınç: Bağlantı Hatası", text_color="#FF6666")
        ruzgar_bilgi.configure(text="Rüzgar: Bağlantı Hatası", text_color="#FF6666")
        rakim_bilgi.configure(text="Rakım: Bağlantı Hatası", text_color="#FF6666")
        durum_bilgi.configure(text="Durum Alınamadı", text_color="#FF6666")
    hava_yenile_btn.configure(text="🔄", fg_color="transparent")

def sehir_degisti(secilen_sehir):
    yeni_ilceler = list(bolge_koordinatlari[secilen_sehir].keys())
    ilce_menu.configure(values=yeni_ilceler)
    ilce_menu.set(yeni_ilceler[0])
    bagimsiz_hava_guncelle()

def baslangic_verilerini_cek():
    bagimsiz_doviz_guncelle()
    bagimsiz_hava_guncelle()

doviz_yenile_btn.configure(command=bagimsiz_doviz_guncelle)
hava_yenile_btn.configure(command=bagimsiz_hava_guncelle)
sehir_menu.configure(command=sehir_degisti)
ilce_menu.configure(command=bagimsiz_hava_guncelle)

app.after(100, baslangic_verilerini_cek)
giris_kutusu.bind('<Return>', hesapla)
app.mainloop()