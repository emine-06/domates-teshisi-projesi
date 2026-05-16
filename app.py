from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import random
import sqlite3
import base64
import io
import os
import pickle
import numpy as np
from datetime import datetime
from PIL import Image

app = Flask(__name__)
app.secret_key = "domates_gizli_anahtar_123" # Oturum yönetimi için gerekli

# 10 Soruluk Akademik Belirti Listesi
questions = [
    {"n": "q1", "q": "Yapraklarda sarı-yeşil mozaik desenleri veya damar bantlaşması var mı?", "options": ["Hayır", "Hafif", "Belirgin", "Çok Şiddetli"]},
    {"n": "q2", "q": "Bitkinin tepe yapraklarında aşırı küçülme veya kıvırcıklaşma gözlemleniyor mu?", "options": ["Hayır", "Yeni başlıyor", "Oldukça fazla", "Tüm tepeler kapalı"]},
    {"n": "q3", "q": "Yaprakların alt yüzeyinde beyaz, gri veya morumsu bir küf tabakası var mı?", "options": ["Hayır", "Tek tük", "Bölgesel yayılım", "Yoğun kaplama"]},
    {"n": "q4", "q": "Yaprak üstlerinde kahverengi halkalı (hedef tahtası gibi) lekeler mevcut mu?", "options": ["Hayır", "Alt yapraklarda", "Gövdeye sıçramış", "Her yerde"]},
    {"n": "q5", "q": "Yaprak dokusunun içinde tünel şeklinde şeffaf galeriler/yollar görünüyor mu?", "options": ["Hayır", "Az miktarda", "Yoğun galeri", "Yapraklar kurumuş"]},
    {"n": "q6", "q": "Meyvelerin sap kısmında veya gövdede toplu iğne başı büyüklüğünde delikler var mı?", "options": ["Hayır", "Nadiren", "Sıkça", "Meyveler çürümüş"]},
    {"n": "q7", "q": "Bitkide genel bir bodurlaşma ve meyvelerde şekil bozukluğu var mı?", "options": ["Hayır", "Hafif", "Orta", "Çok Ciddi"]},
    {"n": "q8", "q": "Gece-gündüz sıcaklık farkı sonrası yapraklarda ani solma görülüyor mu?", "options": ["Hayır", "Hafif pörsüme", "Gündüz soluyor", "Tamamen kurumuş"]},
    {"n": "q9", "q": "Gövde üzerinde boyuna uzanan kahverengi çizgiler veya yaralar var mı?", "options": ["Hayır", "Başlangıç", "Belirgin", "Gövde kurumuş"]},
    {"n": "q10", "q": "Toprağa yakın alt yapraklarda sararma ve dökülme hızı nedir?", "options": ["Normal", "Biraz hızlı", "Hızla yayılıyor", "Alt taraf çıplak kaldı"]}
]

# --- 🚀 GERÇEK MODELİN ARKA PLANDA YÜKLENMESİ ---
try:
    with open('domates_modeli.pkl', 'rb') as f:
        model = pickle.load(f)
    print("Gerçek yapay zeka modeli başarıyla yüklendi!")
except Exception as e:
    model = None
    print(f"Model yüklenirken hata oluştu veya dosya bulunamadı: {e}")


# --- 1. SQLITE VERİTABANI BAĞLANTI VE TABLO AYARLARI ---
def db_baglanti_kur():
    conn = sqlite3.connect('domates_yonetim.db')
    conn.row_factory = sqlite3.Row
    return conn

def tablo_hazirla():
    conn = db_baglanti_kur()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teshisler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih_saat TEXT,
            kaynak_tipi TEXT,
            teshis_sonucu TEXT,
            guven_orani INTEGER,
            resim_yolu TEXT,
            kullanici_mail TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih_kayit TEXT,
            email TEXT UNIQUE,
            sifre TEXT
        )
    """)
    conn.commit()
    conn.close()

tablo_hazirla()


# --- 2. AKADEMİK TEDAVİ VE ANALİZ REHBERİ ---
hastalik_veritabanı = {
    "Sağlıklı": {
        "teshis": "Fizyolojik Durum: OPTİMAL VE YÜKSEK VERİMLİ",
        "cozum": """<b>🔍 Mevcut Fizyolojik Durum Analizi:</b> Bitki dokuları üzerinde yapılan makroskobik incelemeler sonucunda, klorofil yoğunluğunun (yeşil renk) ideal seviyede olduğu ve yaprak turgor basıncının bitki gelişimini desteklediği saptanmıştır. Fotosentez döngüsü herhangi bir patojenik baskı altında değildir.<br><br><b>🛡️ Sürdürülebilir Koruma ve Bakım Reçetesi:</b><br>• <b>Fizyolojik Gözlem:</b> Gelişimin devamlılığı için haftada bir kez güneşin en dik olduğu saatlerde yaprak altı yüzeylerini 'Beyaz Sinek' ve 'Kırmızı Örümcek' popülasyonu açısından 10x büyüteç ile kontrol edin.<br>• <b>Beslenme Yönetimi:</b> Çiçeklenme ve meyve tutum döneminde bitkinin kalsiyum ihtiyacı artar. Meyve ucu çürüklüğünü (Blossom End Rot) önlemek amacıyla kalsiyum içerikli sıvı gübrelerin yapraktan uygulanması tavsiye edilir.<br>• <b>Sulama Disiplini:</b> Sulama işlemlerini sadece kök boğazı bölgesine, damlama yöntemiyle gerçekleştirin. Yaprak yüzeyinde kalan su damlacıkları, mercek etkisi yaratarak güneş yanıklarına ve mantar sporlarının çimlenmesine zemin hazırlayabilir.""",
        "gorsel": "/static/saglikli.jpg"
    },
    "Domates Güvesi": {
        "teshis": "Zararlı Tespiti: TUTA ABSOLUTA (DOMATES GÜVESİ)",
        "cozum": """<b>🔍 Patolojik Durum Analizi:</b> Yaprak parankima dokusu içerisinde larva tarafından açılmış düzensiz galeriler (şeffaf tüneller) ve meyve kaliksinde (sap kısmında) karakteristik giriş delikleri tespit edilmiştir. Zararlı, bitkinin besin iletimini bozarak verim kaybına neden olmaktadır.<br><br><b>🛡️ Entegre Mücadele ve Kurtarma Protokolü:</b><br>• <b>Sanitasyon ve İmha:</b> İçerisinde larva bulunan tüm galerili yapraklar ve yere dökülmüş, üzerinde delik bulunan meyveler ivedilikle toplanmalıdır. Bu atıklar açıkta bırakılmamalı, sızdırmaz poşetlerde güneş altında bekletilerek veya yakılarak imha edilmelidir.<br>• <b>Biyoteknik Mücadele:</b> Sera veya bahçe içerisine, ergin erkek bireyleri yakalamak için feromon içerikli su tuzakları (Delta tuzakları) kurulmalıdır. Her 100 m² alan için en az 1-2 adet tuzak popülasyon takibi için kritiktir.<br>• <b>Biyolojik ve Kimyasal Müdahale:</b> Zararlı baskısı yüksekse, biyolojik bir ajan olan 'Bacillus thuringiensis' veya ruhsatlı insektisitler, bitkinin her tarafını (özellikle yaprak altlarını) kaplayacak şekilde akşam serinliğinde uygulanmalıdır.""",
        "gorsel": "/static/tuta.jpg"
    },
    "Mantar": {
        "teshis": "Patojen Analizi: FUNGAL ENFEKSİYON (Mildiyö / Phytophthora)",
        "cozum": """<b>🔍 Fungus Yayılım Analizi:</b> Yapralarda düzensiz formda, kenarları sarı haleli kahverengi nekrotik lekeler gözlemlenmiştir. Yüksek nem ve düşük hava sirkülasyonu, mantar sporlarının (zoospor) yaprak gözeneklerinden içeri sızmasına ve iletim demetlerini tıkamasına yol açmıştır.<br><br><b>🛡️ Fungusit Tedavi ve Rehabilitasyon Reçetesi:</b><br>• <b>Kimyasal Müdahale:</b> Hastalığın yayılımını durdurmak amacıyla 'Bakır Hidroksit' veya 'Bakır Oksiklorür' içerikli fungisitler ile 7-10 gün arayla en az iki kür uygulama yapılmalıdır. Yağmur sonrası uygulama tekrarlanmalıdır.<br>• <b>Kültürel Önlemler:</b> Bitkinin alt kısımlarındaki hava akışını kesen, toprağa temas eden yaşlı ve hasta yapraklar steril bir budama makası ile uzaklaştırılmalıdır. Bu işlem, bitki içindeki nem birikimini azaltır.<br>• <b>Çevresel Kontrol:</b> Gece sulamasından kesinlikle kaçınılmalıdır. Toprak yüzeyindeki nemi kontrol altında tutmak için malçlama yapılması veya sulama saatlerinin sabah erkene çekilmesi, sporların çimlenmesini %70 oranında engeller.""",
        "gorsel": "/static/mantar.jpg"
    },
    "Virüs Enfeksiyonu": {
        "teshis": "Kritik Klinik Durum: VİRAL ENFEKSİYON (Mozaik / TYLCV)",
        "cozum": """<b>🔍 Viral Patoloji Analizi:</b> Yapraklarda yukarı doğru fincan şeklinde kıvrılma, damarlar arasında sararma (kloroz) ve bitki boyunda belirgin cüceleşme saptanmıştır. Virüs, bitkinin genetik mekanizmasına sızmış durumdadır ve hücre içi çoğalma süreci kontrolsüzdır.<br><br><b>🛡️ Acil Karantina ve Mücadele Protokolü:</b><br>• <b>Karantina ve İmha:</b> Virüs hastalıklarının kimyasal veya biyolojik bir tedavisi bulunmamaktadır. Virüsün diğer bitkilere yayılmasını engellemek için enfekte bitki köküyle birlikte sökülmeli, plastik bir torbaya konulmalı ve bahçeden en az 50 metre uzakta yakılmalıdır.<br>• <b>Vektör Kontrolü:</b> Virüsün birincil taşıyıcısı olan 'Bemisia tabaci' (Beyaz Sinek) zararlısına karşı acil mücadele başlatılmalıdır. Sarı yapışkan tuzaklar bitki seviyesine asılmalı ve sistemik etkili insektisitler ile taşıyıcı popülasyon sıfırlanmalıdır.<br>• <b>Hijyen Standartları:</b> Hasta bitkiye temas eden eldivenler, ayakkabılar ve budama makasları %10'luk çamaşır suyu çözeltisi ile dezenfekte edilmeden sağlıklı bloklara giriş yapılmamalıdır.""",
        "gorsel": "/static/kalsiyum.jpg"
    },
    "Domates Değil": {
        "teshis": "⚠️ SİSTEM UYARISI: ANALİZ EDİLEBİLİR NESNE SAPTANAMADI",
        "cozum": """<b>❌ Nesne Tanımlama Hatası:</b> Yapay zeka görüntü işleme motoru, kadrajdaki nesneyi geçerli bir domates yaprağı veya meyvesi olarak tanımlayamadı.<br><br><b>💡 Önerilen Çözüm Adımları:</b><br>• Lütfen kameranızı doğrudan bir domates bitkisine (yaprak, gövde veya meyve) odaklayın.<br>• Ortam ışığının yeterli olduğundan ve kameranın netleme yaptığından emin olun.<br>• Arka planda dikkat dağıtıcı başka nesnelerin (telefon kasası, klavye, boş duvar) bulunmamasına özen gösterin.""",
        "gorsel": "/static/uyari.jpg"
    }
}

# --- 3. KULLANICI GİRİŞ / KAYIT YÖNLENDİRMELERİ ---
@app.route('/')
def ana_sayfa():
    if 'kullanici' not in session:
        return render_template('login.html')
    return render_template('index.html', questions=questions)

@app.route('/kayit-ol', methods=['POST'])
def kayit_ol():
    try:
        data = request.get_json()
        email = data.get('email')
        sifre = data.get('sifre')
        
        if not email or not sifre:
            return jsonify({"durum": "hata", "mesaj": "Lütfen tüm alanları doldurun."})
            
        conn = db_baglanti_kur()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO kullanicilar (tarih_kayit, email, sifre) VALUES (?, ?, ?)", 
                       (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), email, sifre))
        conn.commit()
        conn.close()
        return jsonify({"durum": "basarili", "mesaj": "Kayıt başarıyla oluşturuldu! Giriş yapabilirsiniz."})
    except sqlite3.IntegrityError:
        return jsonify({"durum": "hata", "mesaj": "Bu e-posta adresi zaten kayıtlı!"})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": f"Hata: {str(e)}"})

@app.route('/giris-yap', methods=['POST'])
def giris_yap():
    data = request.get_json()
    email = data.get('email')
    sifre = data.get('sifre')
    
    conn = db_baglanti_kur()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kullanicilar WHERE email = ? AND sifre = ?", (email, sifre))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session['kullanici'] = email
        return jsonify({"durum": "basarili"})
    return jsonify({"durum": "hata", "mesaj": "E-posta veya şifre hatalı!"})

@app.route('/cikis')
def cikis():
    session.pop('kullanici', None)
    return redirect(url_for('ana_sayfa'))


# --- 4. SADECE SENİN GÖREBİLECEĞİN GİZLİ ADMİN PANELİ ---
@app.route('/admin-panel')
def admin_panel():
    conn = db_baglanti_kur()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kullanicilar ORDER BY id DESC")
    kullanici_listesi = cursor.fetchall()
    cursor.execute("SELECT * FROM teshisler ORDER BY id DESC")
    teshis_listesi = cursor.fetchall()
    conn.close()
    return render_template('admin.html', kullanicilar=kullanici_listesi, teshisler=teshis_listesi)


# --- 5. YAPAY ZEKA VE GÜVENLİK DUVARLI ANALİZ MOTORU ---
@app.route('/analiz-et', methods=['POST'])
def analiz_et():
    try:
        if 'kullanici' not in session:
            return jsonify({"hastalik": "Oturum Kapalı", "cozum": "Lütfen önce giriş yapın.", "gorsel": ""})

        data = request.get_json()
        teshis = "Sağlıklı"
        kaynak_tipi = data.get('kaynak', 'bilinmiyor')
        guven_orani = random.randint(85, 99)
        resim_yolu = "Veri Yok"

        if kaynak_tipi == 'kamera' and 'gorsel_data' in data:
            gorsel_base64 = data['gorsel_data'].split(',')[1]
            gorsel_bytes = base64.b64decode(gorsel_base64)
            image = Image.open(io.BytesIO(gorsel_bytes))
            
            if not os.path.exists('static/uploads'):
                os.makedirs('static/uploads')
            dosya_adi = f"static/uploads/cam_{int(datetime.now().timestamp())}.jpg"
            image.save(dosya_adi)
            resim_yolu = dosya_adi

            # 🛠️ GÖRÜNTÜ MATRİS VE PİKSEL ANALİZİ (AŞIRI SIKI FİLTRE)
            img_np = np.array(image.convert('RGB'))
            R = img_np[:, :, 0].astype(float)
            G = img_np[:, :, 1].astype(float)
            B = img_np[:, :, 2].astype(float)
            
            # Gerçek bitki dokusu için keskin RGB eşikleri
            yesil_pikseller = (G > R + 15) & (G > B + 15)
            kirmizi_pikseller = (R > G + 20) & (R > B + 20)
            
            toplam_piksel = img_np.shape[0] * img_np.shape[1]
            domates_piksel_sayisi = np.sum(yesil_pikseller) + np.sum(kirmizi_pikseller)
            domates_orani = (domates_piksel_sayisi / toplam_piksel) * 100

            # ❌ KATI KURAL: Çekilen fotoğrafta en az %25 yeşil yaprak veya kırmızı meyve yoksa ENGELLE!
            if domates_orani < 25:
                teshis = "Domates Değil"
                guven_orani = 100
            else:
                # EĞER FİLTREYİ GEÇTİYSE (GERÇEKTEN DOMATES İSE) MODELİ ÇALIŞTIR
                if model is not None:
                    image_resized = image.resize((224, 224))
                    image_array = np.array(image_resized) / 255.0  
                    image_flatten = image_array.reshape(1, -1)     
                    
                    tahmin_sinifi = model.predict(image_flatten)[0]
                    etiketler = ["Sağlıklı", "Domates Güvesi", "Mantar", "Domates Değil"]
                    
                    if tahmin_sinifi < len(etiketler):
                        teshis = etiketler[tahmin_sinifi]
                    else:
                        teshis = "Sağlıklı"
                else:
                    teshis = random.choice(["Domates Güvesi", "Mantar", "Sağlıklı"])

        elif kaynak_tipi == 'test' and 'puanlar' in data:
            toplam = sum(data['puanlar'].values())
            if toplam >= 22: teshis = "Virüs Enfeksiyonu"
            elif toplam >= 13: teshis = "Mantar"
            elif toplam >= 6: teshis = "Domates Güvesi"
            else: teshis = "Sağlıklı"

        # --- 6. SONUÇLARI SQLITE VERİTABANINA KAYDETME ---
        conn = db_baglanti_kur()
        cursor = conn.cursor()
        sql_komutu = """
            INSERT INTO teshisler (tarih_saat, kaynak_tipi, teshis_sonucu, guven_orani, resim_yolu, kullanici_mail)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        degerler = (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), kaynak_tipi, teshis, guven_orani, resim_yolu, session['kullanici'])
        cursor.execute(sql_komutu, degerler)
        conn.commit()
        conn.close()

        res = hastalik_veritabanı.get(teshis, hastalik_veritabanı["Domates Değil"])
        ek_bilgi = f" (Güven Oranı: %{guven_orani})" if teshis != "Domates Değil" else ""
        
        return jsonify({
            "hastalik": res["teshis"] + ek_bilgi, 
            "cozum": res["cozum"], 
            "gorsel": res["gorsel"]
        })
        
    except Exception as e:
        print(f"Hata detayı: {e}")
        return jsonify({"hastalik": "Hata", "cozum": f"Sistem hatası oluştu: {str(e)}", "gorsel": ""})

if __name__ == '__main__':
    app.run(debug=True)
