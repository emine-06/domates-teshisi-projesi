const video = document.getElementById('webcam');
const canvas = document.getElementById('snapshot');
const captureBtn = document.getElementById('capture-btn');
const resultPanel = document.getElementById('result-panel');
const statusTitle = document.getElementById('status-title');
const diseaseName = document.getElementById('disease-name');
const diseaseDesc = document.getElementById('disease-desc');

// 1. Gerçek Kamerayı Başlatma Fonksiyonu
async function startCamera() {
    try {
        // 'environment' parametresi telefonlarda arka kamerayı, bilgisayarda varsayılan kamerayı açar
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: "environment" }, 
            audio: false 
        });
        video.srcObject = stream;
    } catch (err) {
        console.error("Kamera erişim hatası: ", err);
        alert("Kameranıza erişilemedi. Lütfen izin verdiğinizden emin olun.");
    }
}

// 2. Butona Basıldığında Fotoğraf Çekme Mantığı
captureBtn.addEventListener('click', () => {
    const context = canvas.getContext('2d');
    
    // Video boyutlarını canvas'a aktar
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Videodaki anlık kareyi canvas üzerine çiz (Fotoğrafı yakala)
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Yakalanan fotoğrafı Yapay Zekaya göndermek için base64 formatına çeviriyoruz
    const base64Image = canvas.toDataURL('image/jpeg');
    
    // Sonuç panelini görünür yap ve yükleniyor de
    resultPanel.style.display = 'block';
    statusTitle.innerText = "Durum: Analiz Ediliyor...";
    diseaseName.innerText = "Lütfen bekleyin...";
    diseaseDesc.innerText = "Görüntü işleniyor...";

    // Sunucuya gönderme fonksiyonunu tetikle
    sendToBackend(base64Image);
});

// 3. Arka Plana (Python/Flask) Veri Gönderme (Şimdilik Geçici Mantık)
function sendToBackend(imageData) {
    // NOT: Burayı bir sonraki adımda Python kodumuza (app.py) bağlayacağız.
    // Şimdilik sistemin çalıştığını görmek için simüle ediyoruz:
    setTimeout(() => {
        statusTitle.innerText = "Durum: Analiz Tamamlandı";
        
        // Hoca "kodlama olmasın, sözel mantık olsun" dediği için buradaki kontrolü
        // ileride tamamen Python'dan gelen cevaba göre yöneteceğiz.
        let isTomato = true; // Gerçekte bunu yapay zeka söyleyecek

        if (!isTomato) {
            diseaseName.innerHTML = "<span class='warning'>Uyarı: Bu bir domates değil!</span>";
            diseaseDesc.innerText = "Sistemimiz şu anda sadece domates yaprağı ve meyvesini analiz edebilmektedir. Lütfen kamerayı bir domatese doğrultun.";
        } else {
            diseaseName.innerHTML = "<span class='success'>Domates Güvesi (Tuta Absoluta)</span>";
            diseaseDesc.innerText = "Yapraklarda ve meyvede galeriler açarak zarar verir. Kültürel önlem olarak feromon tuzakları kullanılmalı, kimyasal mücadele için hocanızın önerdiği preparatlar seçilmelidir.";
        }
    }, 1500);
}

// Sayfa yüklenir yüklenmez kamerayı aç
startCamera();