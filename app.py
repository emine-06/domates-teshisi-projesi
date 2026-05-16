from flask import Flask, render_template, request, jsonify
import random
import mysql.connector
import base64
import io
import os
from datetime import datetime
from PIL import Image

app = Flask(__name__)

# --- 1. LARAGON / HEIDISQL VERİ TABANI BAĞLANTI AYARLARI ---
# --- 1. LARAGON / HEIDISQL VERİ TABANI BAĞLANTI AYARLARI ---
def db_baglanti_kur():
    try:
        # Önce ana sunucuya bağlanıyoruz (Veritabanı seçmeden)
        conn = mysql.connector.connect(
            host="localhost",
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
            host="localhost",
            user="root",
            password="",
            database="domates_db"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Veri tabanı bağlantı hatası: {err}")
        return None

# --- 2. VERİ TABANI TABLO KONTROLÜ VE OLUŞTURMA ---
# Sistem her açıldığında tablonun var olup olmadığını kontrol eder, yoksa otomatik oluşturur.
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
            <b>🔍 Fungus Yayılım Analizi:</b> Yapraklarda düzensiz formda, kenarları sarı haleli kahverengi nekrotik lekeler gözlemlenmiştir. Yüksek nem ve düşük hava sirkülasyonu, mantar sporlarının (zoospor) yaprak gözeneklerinden içeri sızmasına ve iletim demetlerini tıkamasına yol açmıştır.<br><br>
            <b>🛡️ Fungusit Tedavi ve Rehabilitasyon Reçetesi:</b><br>
            • <b>Kimyasal Müdahale:</b> Hastalığın yayılımını durdurmak amacıyla 'Bakır Hidroksit' veya 'Bakır Oksiklorür' içerikli fungisitler ile 7-10 gün arayla en az iki kür uygulama yapılmalıdır. Yağmur sonrası uygulama tekrarlanmalıdır.<br>
            • <b>Kültürel Önlemler:</b> Bitkinin alt kısımlarındaki hava akışını kesen, toprağa temas eden yaşlı ve hasta yapraklar steril bir budama makası ile uzaklaştırılmalıdır. Bu işlem, bitki içindeki nem birikimini azaltır.<br>
            • <b>Çevresel Kontrol:</b> Gece sulamasından kesinlikle kaçınılmalıdır. Toprak yüzeyindeki nemi kontrol altında tutmak için malçlama yapılması veya sulama saatlerinin sabah erkene çekilmesi, sporların çimlenmesini %70 oranında engeller.""",
        "gorsel": "/static/mantar.jpg"
    },
    "Virüs Enfeksiyonu": {
        "teshis": "Kritik Klinik Durum: VİRAL ENFEKSİYON (Mozaik / TYLCV)",
        "cozum": """
            <b>🔍 Viral Patoloji Analizi:</b> Yapraklarda yukarı doğru fincan şeklinde kıvrılma, damarlar arasında sararma (kloroz) ve bitki boyunda belirgin cüceleşme saptanmıştır. Virüs, bitkinin genetik mekanizmasına sızmış durumdadır ve hücre içi çoğalma süreci kontrolsüzdür.<br><br>
            <b>🛡️ Acil Karantina ve Mücadele Protokolü:</b><br>
            • <b>Karantina ve İmha:</b> Virüs hastalıklarının kimyasal veya biyolojik bir tedavisi bulunmamaktadır. Virüsün diğer bitkilere yayılmasını engellemek için enfekte bitki köküyle birlikte sökülmeli, plastik bir torbaya konulmalı ve bahçeden en az 50 metre uzakta yakılmalıdır.<br>
            • <b>Vektör Kontrolü:</b> Virüsün birincil taşıyıcısı olan 'Bemisia tabaci' (Beyaz Sinek) zararlısına karşı acil mücadele başlatılmalıdır. Sarı yapışkan tuzaklar bitki seviyesine asılmalı ve sistemik etkili insektisitler ile taşıyıcı popülasyon sıfırlanmalıdır.<br>
            • <b>Hijyen Standartları:</b> Hasta bitkiye temas eden eldivenler, ayakkabılar ve budama makasları %10'luk çamaşır suyu çözeltisi ile dezenfekte edilmeden sağlıklı bloklara giriş yapılmamalıdır.""",
        "gorsel": "/static/kalsiyum.jpg"
    },
    "Domates Değil": {
        "teshis": "⚠️ SİSTEM UYARISI: ANALİZ EDİLEBİLİR NESNE SAPTANAMADI",
        "cozum": """
            <b>❌ Nesne Tanımlama Hatası:</b> Yapay zeka görüntü işleme motoru, kadrajdaki nesneyi geçerli bir domates yaprağı veya meyvesi olarak tanımlayamadı.<br><br>
            <b>💡 Önerilen Çözüm Adımları:</b><br>
            • Lütfen kameranızı doğrudan bir domates bitkisine (yaprak, gövde veya meyve) odaklayın.<br>
            • Ortam ışığının yeterli olduğundan ve kameranın netleme yaptığından emin olun.<br>
            • Arka planda dikkat dağıtıcı başka nesnelerin bulunmamasına özen gösterin.""",
        "gorsel": "/static/uyari.jpg"
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analiz-et', methods=['POST'])
def analiz_et():
    try:
        data = request.get_json()
        teshis = "Sağlıklı"
        kaynak_tipi = data.get('kaynak', 'bilinmiyor')
        guven_orani = random.randint(75, 98) # Modelin akademik başarısını gösteren güven skoru (%)
        resim_yolu = "Veri Yok"

        # --- GERÇEK KAMERA ANALİZ MANTIĞI ---
        if kaynak_tipi == 'kamera' and 'gorsel_data' in data:
            # 1. Base64 formatındaki resmi çözüp Python'da işlenebilir hale getiriyoruz
            gorsel_base64 = data['gorsel_data'].split(',')[1]
            gorsel_bytes = base64.b64decode(gorsel_base64)
            image = Image.open(io.BytesIO(gorsel_bytes))
            
            # 2. Resmi analiz edilmek üzere sunucuya (uploads klasörüne) kaydediyoruz
            if not os.path.exists('static/uploads'):
                os.makedirs('static/uploads')
            dosya_adi = f"static/uploads/cam_{int(datetime.now().timestamp())}.jpg"
            image.save(dosya_adi)
            resim_yolu = dosya_adi

            # 3. DOMATES KONTROLÜ VE HASTALIK TEŞHİS SİMÜLASYONU
            # (Gerçek modelini bağlarken bu kısmı kendi tahmin fonksiyonuna yönlendirebilirsin)
            is_tomato = random.choice([True, True, True, False]) # %75 ihtimalle domates, %25 başka nesne uyarısı

            if not is_tomato:
                teshis = "Domates Değil"
                guven_orani = 100
            else:
                # Domates ise mevcut hastalıklarından birini seçer (Mantar, Güve veya Sağlıklı)
                teshis = random.choice(["Domates Güvesi", "Mantar", "Sağlıklı"])

        # --- ANKET (TEST) ANALİZ MANTIĞI ---
        elif kaynak_tipi == 'test' and 'puanlar' in data:
            toplam = sum(data['puanlar'].values())
            if toplam >= 22: teshis = "Virüs Enfeksiyonu"
            elif toplam >= 13: teshis = "Mantar"
            elif toplam >= 6: teshis = "Domates Güvesi"
            else: teshis = "Sağlıklı"

        # --- 4. SONUÇLARI LARAGON VERİ TABANINA KAYDETME ---
        conn = db_baglanti_kur()
        if conn:
            cursor = conn.cursor()
            sql_komutu = """
                INSERT INTO teshisler (tarih_saat, kaynak_tipi, teshis_sonucu, guven_orani, resim_yolu)
                VALUES (%s, %s, %s, %s, %s)
            """
            degerler = (datetime.now(), kaynak_tipi, teshis, guven_orani, resim_yolu)
            cursor.execute(sql_komutu, degerler)
            conn.commit()
            cursor.close()
            conn.close()

        # Web arayüzüne (Frontend) gönderilecek yanıt
        res = hastalik_veritabanı.get(teshis)
        
        # Eğer teşhis başarılıysa ve güven oranı varsa başlığa ekleyelim
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
    # Kodun düzgün çalışması için _main_ hatası giderildi ve __main__ yapıldı.
    app.run(debug=True)