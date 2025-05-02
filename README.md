# TurkPatent Marka Araştırma Otomasyon Servisi

## Proje Açıklaması

Bu proje, Türk Patent ve Marka Kurumu'nun (TÜRKPATENT) web sitesindeki marka araştırma fonksiyonunu otomatikleştirmeyi amaçlayan deneysel bir servistir. Proje, belirtilen marka adları için arama yapma, sonuçları çekme ve potansiyel benzerlikleri tespit etme (geliştirme aşamasında) yeteneklerine sahip olmayı hedefler.

**Önemli Not:** Bu proje, TÜRKPATENT'in herkese açık web arayüzünü programatik olarak kullanmaktadır. Resmi bir API entegrasyonu değildir.

## ⚠️ Yasal, Etik ve Teknik Uyarılar ⚠️

Bu projeyi kullanmadan veya geliştirmeye katkıda bulunmadan önce aşağıdaki maddeleri **mutlaka** okuyun ve anlayın:

1.  **Web Kazıma (Web Scraping) Riskleri:** Kamu kurumlarının web sitelerini otomatik araçlarla kazımak, sitenin kullanım koşullarına aykırı olabilir. Bu durum yasal sonuçlar doğurabilir. Lütfen TÜRKPATENT web sitesinin kullanım koşullarını dikkatlice inceleyin. Bu projenin amacı eğitim veya kişisel araştırma olabilir, ancak yasa dışı veya etik olmayan faaliyetler için kullanılmamalıdır. Projeyi kullanmanın tüm sorumluluğu size aittir.
2.  **Anti-Bot Önlemleri:** TÜRKPATENT web sitesi, otomatik erişimi engellemek için dinamik tokenler, CAPTCHA'lar ve diğer anti-bot mekanizmaları kullanmaktadır. Proje, bu önlemleri aşmaya yönelik teknikler (headless browser kullanımı gibi) içerebilir, ancak bu yöntemler sürekli olarak güncellenen sitelere karşı kırılgan olabilir.
3.  **Sitenin Yapısal Değişiklikleri:** TÜRKPATENT web sitesinin arayüzünde veya arama mekanizmasında yapılacak herhangi bir değişiklik, projenin çalışmamasına neden olacaktır. Kodun sürekli olarak güncel tutulması ve bakımının yapılması gerekebilir.
4.  **Veri Doğruluğu:** Otomatik olarak çekilen verinin doğruluğu garanti edilmez. Resmi marka araştırmaları ve hukuki süreçler için her zaman TÜRKPATENT'in resmi kanallarını ve bültenlerini kullanmalısınız.
5.  **Sunucu Yükü:** Otomatik ve kontrolsüz istekler göndermek, kamu hizmeti sunan TÜRKPATENT sunucularına aşırı yük bindirebilir. Lütfen sorumlu davranın ve istekler arasına yeterli gecikmeler koyun.
6.  **Benzerlik Analizi Karmaşıklığı:** Projenin hedeflediği benzerlik analizi kısmı, sadece teknik bir veri işleme değil, aynı zamanda hukuki yorum da gerektiren karmaşık bir alandır. Otomatik analiz sonuçları profesyonel hukuki danışmanlığın yerine geçmez.

**Bu projeyi kullanarak veya forklayarak yukarıdaki riskleri ve sorumlulukları kabul etmiş sayılırsınız. Proje yazarları herhangi bir yanlış kullanım veya yasal sonuçtan sorumlu tutulamaz.**

## Özellikler (Geliştirme Hedefleri)

* Belirtilen bir marka adı için TÜRKPATENT veri tabanında arama yapma.
* Arama sonuçlarını (marka adı, numara, sınıf, durum vb.) çekme ve yapısal hale getirme.
* Dinamik token gibi site gereksinimlerini yönetme (headless browser kullanımı ile).
* Markaların detay bilgilerini çekme (Opsiyonel).
* Çekilen markalar arasında potansiyel benzerlikleri tespit etme (Metin, fonetik vb. analizi).
* Bir web servisi (API endpoint) üzerinden arama ve sonuç sunma.

## Kullanılan Teknolojiler

* Python
* Web Servis Framework'ü (FastAPI veya Flask)
* Headless Browser Otomasyonu (Playwright önerilir)
* HTTP İstek Kütüphanesi (requests)
* HTML/JSON Ayrıştırma Kütüphanesi (BeautifulSoup, lxml veya Python'ın json kütüphanesi)
* Benzerlik Analizi Kütüphaneleri (NLP, fuzzy matching vb. kütüphaneler)

## Kurulum

**(Bu bölüm proje geliştikçe doldurulacaktır. Temel adımlar şunları içerecektir):**

1.  Bu repoyu klonlayın:
    ```bash
    git clone [https://github.com/KULLANICI_ADINIZ/turkpatent-trademark-scraper.git](https://github.com/KULLANICI_ADINIZ/turkpatent-trademark-scraper.git)
    cd turkpatent-trademark-scraper
    ```
2.  Python sanal ortamı oluşturun ve aktive edin.
3.  Bağımlılıkları yükleyin:
    ```bash
    pip install -r requirements.txt
    ```
4.  Playwright tarayıcılarını kurun:
    ```bash
    playwright install
    ```
5.  Gerekli konfigürasyonları yapın (config.yaml dosyası kullanılacaksa).

## Kullanım

**(Bu bölüm proje geliştikçe doldurulacaktır. Örnek kullanımlar şunları içerecektir):**

* Servisi çalıştırma komutu.
* Servisin API endpoint'ine örnek istek gönderme (curl veya Postman ile).
* Benzerlik analizi ayarlamaları (varsa).

## Proje Yapısı

**(Bu bölüm, yukarıda önerilen dosya yapısı açıklanacaktır.)**

* `src/`: Ana uygulama kodlarını içerir.
    * `scraper.py`: Web kazıma ve veri çekme mantığı.
    * `analyzer.py`: Marka benzerliği analizi algoritmaları.
    * `service.py`: Web servisi (API) endpoint tanımları.
    * `utils.py`: Ortak kullanılan yardımcı fonksiyonlar.
* `tests/`: Proje testleri.
* `.gitignore`: Git versiyon kontrolüne dahil edilmeyecek dosyalar.
* `Dockerfile`: Uygulamayı containerize etmek için.
* `requirements.txt`: Python bağımlılıkları listesi.
* `README.md`: Proje açıklaması (Bu dosya).
* `config.yaml`: Yapılandırma ayarları (isteğe bağlı).

## Katkıda Bulunma

Katkılarınız memnuniyetle karşılanır! Lütfen bir Pull Request göndermeden önce açık bir Issue oluşturarak yapmayı düşündüğünüz değişiklikleri belirtin.

## Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakın.

---
