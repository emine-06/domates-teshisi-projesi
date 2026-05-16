from flask import Flask, render_template, request, jsonify
import random
import mysql.connector
import base64
import io
import os
import pickle
import numpy as np
from datetime import datetime
from PIL import Image

app = Flask(__name__)

# --- 🚀 [YENİ] GERÇEK MODELİN ARKA PLANDA YÜKLENMESİ ---
try:
    with open('domates_modeli.pkl', 'rb') as f:
        model = pickle.load(f)
    print("Gerçek yapay zeka modeli başarıyla yüklendi!")
except Exception as e:
    model = None
    print(f"Model yüklenirken hata oluştu veya dosya bulunamadı: {e}")


# --- 1. LARAGON / HEIDISQL VERİ TABANI BAĞLANTI AYARLARI ---
def db_baglanti_kur():
    try:
        # [GÜNCELLEME] Render'daki DB_HOST ortam değişkenini okur, yoksa localhost'a bağlanır
        db_host = os.environ.get('DB_HOST', 'localhost')
        
        # Önce ana sunucuya bağlanıyoruz (Veritabanı seçmeden)
        conn = mysql.connector.connect(
            host=db_host,
            user="root",
            password=""
        )
        cursor = conn.cursor()
        # Eğer domates_db yoksa otomatik olarak oluştur emri veriyoruz!
        cursor.execute("CREATE DATABASE IF NOT EXISTS domates_db")
        cursor.close()
        conn.close()

        # Şimdi oluşturulan veritabanına bağlanıp geri döndürüyoruz
        conn = mysql.connector.connect(
            host=db_host,
            user="root",
            password="",
            database="domates_db"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Veri tabanı bağlantı hatası: {err}")
        return None

# --- 2. VERİ TABANI TABLO KONTROLÜ VE OLUŞTURMA ---
def tablo_hazirla():
    conn = db_baglanti_kur()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teshisler (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tarih_saat DATETIME,
                kaynak_tipi VARCHAR(20),
                teshis_sonucu VARCHAR(100),
                guven_orani INT,
                resim_yolu VARCHAR(255)
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

tablo_hazirla()


# --- 3. AKADEMİK TEDAVİ VE ANALİZ REHBERİ (MAKSİMUM DETAY) ---
hastalik_veritabanı = {
    "Sağlıklı": {
        "teshis": "Fizyolojik Durum: OPTİMAL VE YÜKSEK VERİMLİ",
        "cozum": """
            <b>🔍 Mevcut Fizyolojik Durum Analizi:</b> Bitki dokuları üzerinde yapılan makroskobik incelemeler sonucunda, klorofil yoğunluğunun (yeşil renk) ideal seviyede olduğu ve yaprak turgor basıncının bitki gelişimini desteklediği saptanmıştır. Fotosentez döngüsü herhangi bir patojenik baskı altında değildir.<br><br>
            <b>🛡️ Sürdürülebilir Koruma ve Bakım Reçetesi:</b><br>
            • <b>Fizyolojik Gözlem:</b> Gelişimin devamlılığı için haftada bir kez güneşin en dik olduğu saatlerde yaprak altı yüzeylerini 'Beyaz Sinek' ve 'Kırmızı Örümcek' popülasyonu açısından 10x büyüteç ile kontrol edin.<br>
            • <b>Beslenme Yönetimi:</b> Çiçeklenme ve meyve tutum döneminde bitkinin kalsiyum ihtiyacı artar. Meyve ucu çürüklüğünü (Blossom End Rot) önlemek amacıyla kalsiyum içerikli sıvı gübrelerin yapraktan uygulanması tavsiye edilir.<br>
            • <b>Sulama Disiplini:</b> Sulama işlemlerini sadece kök boğazı bölgesine, damlama yöntemiyle gerçekleştirin. Yaprak yüzeyinde kalan su damlacıkları, mercek etkisi yaratarak güneş yanıklarına ve mantar sporlarının çimlenmesine zemin hazırlayabilir.""",
        "gorsel": "/static/saglikli.jpg"
    },
    "Domates Güvesi": {
        "teshis": "Zararlı Tespiti: TUTA ABSOLUTA (DOMATES GÜVESİ)",
        "cozum": """
            <b>🔍 Patolojik Durum Analizi:</b> Yaprak parankima dokusu içerisinde larva tarafından açılmış düzensiz galeriler (şeffaf tüneller) ve meyve kaliksinde (sap kısmında) karakteristik giriş delikleri tespit edilmiştir. Zararlı, bitkinin besin iletimini bozarak verim kaybına neden olmaktadır.<br><br>
            <b>🛡️ Entegre Mücadele ve Kurtarma Protokolü:</b><br>
            • <b>Sanitasyon ve İmha:</b> İçerisinde larva bulunan tüm galerili yapraklar ve yere dökülmüş, üzerinde delik bulunan meyveler ivedilikle toplanmalıdır. Bu atıklar açıkta bırakılmamalı, sızdırmaz poşetlerde güneş altında bekletilerek veya yakılarak imha edilmelidir.<br>
            • <b>Biyoteknik Mücadele:</b> Sera veya bahçe içerisine, ergin erkek bireyleri yakalamak için feromon içerikli su tuzakları (Delta tuzakları) kurulmalıdır. Her 100 m² alan için en az 1-2 adet tuzak popülasyon takibi için kritiktir.<br>
            • <b>Biyolojik ve Kimyasal Müdahale:</b> Zararlı baskısı yüksekse, biyolojik bir ajan olan 'Bacillus thuringiensis' veya ruhsatlı insektisitler, bitkinin her tarafını (özellikle yaprak altlarını) kaplayacak şekilde akşam serinliğinde uygulanmalıdır.""",
        "gorsel": "/static/tuta.jpg"
    },
    "Mantar": {
        "teshis": "Patojen Analizi: FUNGAL ENFEKSİYON (Mildiyö / Phytophthora)",
        "cozum": """
            <b>🔍 Fungus Yayılım Analizi:</b> Yapralarda düzensiz formda, kenarları sarı haleli kahverengi nekrotik lekeler gözlemlenmiştir. Yüksek nem ve düşük hava sirkülasyonu, mantar sporlarının (zoospor) yaprak gözeneklerinden içeri sızmasına ve iletim demetlerini tıkamasına yol açmıştır.<br><br>
            <b>🛡️ Fungusit Tedavi ve Rehabilitasyon Reçetesi:</b><br>
            • <b>Kimyasal Müdahale:</b> Hast
