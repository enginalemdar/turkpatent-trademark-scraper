# src/scraper.py

import json
import asyncio
from playwright.async_api import async_playwright, Page, Browser
import logging
import time
import random

# Logger yapılandırması (isteğe bağlı ama iyi bir pratik)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# TÜRKPATENT Arama Sayfası URL'si
TURKPATENT_SEARCH_URL = "https://www.turkpatent.gov.tr/arastirma-yap"
# API Arama Endpoint'i URL'si (Tespit edildi)
TURKPATENT_API_URL = "https://www.turkpatent.gov.tr/api/research"

# Belirli elementlerin potansiyel selector'ları (Sizin tespitlerinize göre güncellendi!)
# Bunları sitenin güncel yapısına göre test edip doğrulamalısınız!
# Arama kutusu selector'ı: name="searchText" olarak tespit edildi
SEARCH_INPUT_SELECTOR = "input[name='searchText']"
# Sorgula butonu selector'ı: Metin içeriği veya CSS sınıfı ile
SEARCH_BUTTON_SELECTOR = "text=\"SORGULA\"" # Playwright için metin selector'ı
# Alternatif CSS selector denemesi: "button.MuiButton-root.MuiButton-contained"

# Dinamik token veya diğer gizli alanların selector/adı
# Payload'da ana seviyede 'token' olarak gönderildiği tespit edildi.
# Görünmez reCAPTCHA yanıtı olma ihtimali yüksek.
# Standart reCAPTCHA yanıt input'unun adı budur:
RECAPTCHA_RESPONSE_INPUT_NAME = "g-recaptcha-response"

async def get_dynamic_params(page: Page) -> dict:
    """
    Arama sayfasını ziyaret ederek dinamik token ve diğer gerekli parametreleri alır.
    Görünmez reCAPTCHA yanıtını (token) almayı dener.

    Args:
        page: Playwright Page nesnesi.

    Returns:
        Dinamik parametreleri içeren bir dictionary (en azından {'token': '...'} içermeli).
        Parametre alınamazsa boş dictionary veya None dönebilir.
    """
    logging.info(f"Dinamik parametreleri almak için {TURKPATENT_SEARCH_URL} adresine gidiliyor...")
    try:
        # Sayfaya git ve DOM'un yüklenmesini bekle.
        # 'networkidle' reCAPTCHA gibi arka plan isteklerinin tamamlanmasını bekleyebilir,
        # ancak bazen yeterli olmayabilir. Ek bekleme gerekebilir.
        await page.goto(TURKPATENT_SEARCH_URL, wait_until='networkidle')
        logging.info("Arama sayfası yüklendi. Görünmez reCAPTCHA yanıtı (token) aranıyor...")

        # #### Dinamik Token (reCAPTCHA Yanıtı) Alma Mantığı ####
        # Görünmez reCAPTCHA tamamlandığında, genellikle g-recaptcha-response adlı gizli bir input alanına
        # token değerini yazar. Bu alanı bulup değerini çekmeliyiz.
        # reCAPTCHA'nın çalışıp değeri input'a yazması biraz zaman alabilir.
        # Playwright'ın elementin belirli bir duruma gelmesini bekleme özelliğini kullanabiliriz.

        dynamic_token_value = None
        # g-recaptcha-response input alanının value'sunun dolu hale gelmesini bekle
        # Genellikle textarea[name='g-recaptcha-response'] selector'ı kullanılır.
        token_input_selector = f"textarea[name='{RECAPTCHA_RESPONSE_INPUT_NAME}']"
        logging.info(f"reCAPTCHA yanıt input'u bekleniyor: {token_input_selector}")

        try:
            # Belirli bir timeout içinde elementin value'su dolu hale gelene kadar bekle
            # Bu, token'ın JavaScript tarafından yazılmasını bekler.
            # Timeout süresini sitenin ve reCAPTCHA'nın hızına göre ayarlayın (deneme-yanılma).
            # Çok kısa olursa token alınamaz, çok uzun olursa gereksiz bekler.
            await page.wait_for_function(
                f"document.querySelector('{token_input_selector}') && document.querySelector('{token_input_selector}').value.length > 0",
                timeout=20000 # 20 saniye bekle (Ayarlanabilir, gerekirse artırın)
            )

            token_element = await page.query_selector(token_input_selector)
            if token_element:
                 dynamic_token_value = await token_element.get_attribute('value')
                 if dynamic_token_value:
                      logging.info(f"reCAPTCHA token başarıyla yakalandı: {dynamic_token_value[:15]}...") # İlk birkaç karakteri logla
                 else:
                      logging.warning("reCAPTCHA yanıt input alanı bulundu ama value hala boş.")

            # TODO: Eğer yukarıdaki wait_for_function bazen takılıyorsa veya token alınamıyorsa,
            # ek bekleme stratejileri veya farklı selector denemeleri gerekebilir.
            # Örneğin, page.wait_for_selector(token_input_selector) ve sonra kısa bir time.sleep() eklemek.

        except Exception as e:
            # Zaman aşımı veya element bulunamaması hatası
            logging.error(f"reCAPTCHA yanıt input'unu beklerken veya değerini alırken hata/zaman aşımı: {e}")
            logging.error("reCAPTCHA token büyük olasılıkla alınamadı.")
            dynamic_token_value = None # Hata veya zaman aşımı durumunda token yok

        if not dynamic_token_value:
            logging.error("Dinamik reCAPTCHA token alınamadı. Arama yapılamaz.")
            return {} # Token alınamazsa boş dictionary döndür

        logging.info("Dinamik reCAPTCHA token başarıyla alındı.")
        # Payload'daki 'token' anahtarı için bu değeri kullanacağız.
        return {'token': dynamic_token_value}

    except Exception as e:
        logging.error(f"Dinamik parametre alımında genel hata (sayfaya gitme vb.): {e}")
        # Sayfaya gitme hatası, DOM yüklenmeme hatası vb.
        return {}

async def search_trademark(search_text: str, dynamic_params: dict, page: Page) -> list:
    """
    Türk Patent API'sine arama isteği gönderir ve sonuçları çeker.

    Args:
        search_text: Aranacak marka adı.
        dynamic_params: get_dynamic_params fonksiyonundan alınan dinamik parametreler (en az 'token' içermeli).
        page: Playwright Page nesnesi (istek yapmak için kullanılır).

    Returns:
        Marka listesini içeren bir liste (her marka bir dictionary).
        Hata durumunda boş liste döner.
    """
    if not dynamic_params or 'token' not in dynamic_params or not dynamic_params['token']:
        logging.error("Arama yapmak için geçerli dinamik token yok.")
        return []

    logging.info(f"'{search_text}' için arama isteği hazırlanıyor...")

    # #### Payload Yapısı (Sizin tespitinize göre güncellendi) ####
    # Ekran görüntünüzdeki ve paylaştığınız payload yapısına göre oluşturuldu.
    search_payload = {
        "type": "trademark",
        "params": {
            "markTypeId": "0",
            "searchText": search_text, # Kullanıcının girdiği metin
            "searchTextOption": "isContains", # Sabit veya konfigüre edilebilir olmalı ('isContains', 'isStartWith', 'isEquals')
            "holderName": "",
            "holderNameOption": "isStartWith",
            "bulletinNo": "",
            "gazzetteNo": "",
            "clientNo": "",
            # Sınıf arama buraya eklenecek (eğer kullanıcı sınıf da girecekse)
            "niceClasses": [],
            "niceClassesFor": "all"
        },
        "next": 0, # Başlangıç indeksi (Sayfalama için değiştirilecek)
        "limit": 20, # Sayfa boyutu (İsteğe bağlı olarak artırılabilir, sitenin limitine bağlı)
        "order": None, # Sıralama parametreleri buraya eklenebilir eğer kullanılacaksa
        "token": dynamic_params['token'] # Dinamik olarak aldığımız reCAPTCHA token'ı buraya gelecek
    }

    # İstek başlıklarını (headers) gerçek bir tarayıcı gibi ayarlamaya çalışın
    # User-Agent, Referer ve Origin anti-bot için önemli olabilir.
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36", # Gerçekçi ve güncel bir User-Agent kullanın
        "Referer": TURKPATENT_SEARCH_URL, # İsteğin hangi sayfadan geldiği
        "Origin": "https://www.turkpatent.gov.tr", # İsteğin kaynağı
        # Playwright context'i oturum çerezlerini otomatik taşır, manuel Cookie başlığına genellikle gerek kalmaz.
    }

    try:
        # Playwright'ın page.request.post metodunu kullanarak isteği gönder.
        # Bu, Playwright tarayıcısının mevcut oturumunu (çerezler, başlıklar) kullanır.
        logging.info(f"POST isteği gönderiliyor: {TURKPATENT_API_URL}")

        # Anti-bot için istek göndermeden önce rastgele kısa bir bekleme
        await page.wait_for_timeout(random.randint(1000, 3000)) # 1 - 3 saniye arası rastgele bekleme

        response = await page.request.post(
            TURKPATENT_API_URL,
            data=json.dumps(search_payload), # Payload Python dict değil, JSON string olmalı
            headers=headers
        )

        logging.info(f"İstek tamamlandı. Durum Kodu: {response.status}")

        # Yanıtı JSON olarak parse edin
        response_json = await response.json()
        # logging.info(f"Ham Yanıt JSON: {json.dumps(response_json, indent=2)}") # Hata ayıklama için tüm yanıtı yazdır

        # #### Yanıt Yapısını Kontrol Etme ve Sonuçları Çekme (Sizin verdiğiniz yapıya göre DÜZELTİLDİ) ####
        # Verdiğiniz başarılı yanıt yapısına göre sonuçlar 'payload' objesinin içinde 'items' listesi olarak geliyor.
        # Hata durumunda ise 'success': false ve 'error': {...} geliyor.

        if not response_json.get('success', False): # 'success' alanı yoksa veya false ise hata var demektir
             error_code = response_json.get('error', {}).get('code', 'UNKNOWN_ERROR')
             error_message = response_json.get('error', {}).get('message', 'Bilinmeyen Hata')
             logging.error(f"Arama API'sinden hata döndü: [{error_code}] {error_message}")
             # Özellikle HUMAN_CHECK_ERROR kontrolü:
             if error_code == "HUMAN_CHECK_ERROR":
                 logging.error("HUMAN_CHECK_ERROR alındı. reCAPTCHA doğru alınamamış veya başka bir anti-bot önlemi tetiklenmiş olabilir.")
                 logging.warning("get_dynamic_params fonksiyonunu ve bekleme sürelerini gözden geçirin.")
             # TODO: Farklı hata kodlarına göre özel işlemler yapılabilir.
             return [] # Hata durumunda boş liste dön

        # Başarılı yanıt durumunda 'payload' objesini ve içindeki 'items' listesini çek
        payload_data = response_json.get('payload', {})
        trademark_results = payload_data.get('items', [])

        # Toplam sonuç sayısını ve sayfalama bilgilerini çek (Sayfalama için lazım olacak)
        total_results = payload_data.get('total', 0)
        next_page_index = payload_data.get('next', None)
        page_limit = payload_data.get('limit', search_payload['limit']) # Varsayılan limit

        logging.info(f"API yanıtından {len(trademark_results)} marka sonucu çekildi (Toplam sonuç: {total_results}).")

        # TODO: Eğer tüm sonuçları çekmek istiyorsanız, total_results, next_page_index ve page_limit
        # bilgilerini kullanarak scrape_turkpatent_trademarks fonksiyonunda veya burada bir döngü kurarak
        # search_payload'daki 'next' parametresini güncelleyip ek istekler gönderme mantığı eklenecek.

        return trademark_results

    except Exception as e:
        logging.error(f"Arama isteği sırasında genel hata: {e}")
        return []

# scrape_turkpatent_trademarks fonksiyonu aynı kalır.
# get_dynamic_params ve search_trademark fonksiyonlarını Playwright context'i içinde sırayla çağırır.

async def scrape_turkpatent_trademarks(search_query: str) -> list:
    """
    Türk Patent web sitesinden marka araştırması yapar.
    Dinamik token alır, arama isteği gönderir ve sonuçları çeker.

    Args:
        search_query: Aranacak marka adı.

    Returns:
        Bulunan markaların listesi.
    """
    logging.info(f"'{search_query}' için tam scraping süreci başlatılıyor.")
    trademark_list = []
    browser: Browser = None # Tanımlama

    # Playwright context'ini başlat
    async with async_playwright() as p:
        # Başsız (headless=True) veya başlı (headless=False) tarayıcıyı başlat
        # Geliştirme ve hata ayıklama sırasında headless=False yapmak tarayıcıyı görmenizi sağlar.
        # Canlıya alırken tekrar headless=True yapmalısınız.
        try:
            browser = await p.chromium.launch(headless=True) # Headless tarayıcı
            # Eğer görsel hata ayıklama yapmak isterseniz:
            # browser = await p.chromium.launch(headless=False, slow_mo=50) # İşlemleri yavaşlatarak izle
            # context = await browser.new_context(viewport={'width': 1280, 'height': 720}) # Belirli boyut ayarlama
            context = await browser.new_context()
            page: Page = await context.new_page()

            logging.info("Playwright tarayıcı başlatıldı ve sayfa oluşturuldu.")

            # 1. Dinamik parametreleri (reCAPTCHA token) al
            # Burası, Playwright'ın reCAPTCHA JS'ini çalıştırmasını ve token üretmesini bekler.
            dynamic_params = await get_dynamic_params(page)

            if not dynamic_params or 'token' not in dynamic_params:
                 logging.error("Dinamik token alınamadığı için arama yapılamıyor. get_dynamic_params fonksiyonunu ve logları kontrol edin.")
                 return [] # Token alınamadıysa dur

            # 2. Arama isteğini gönder ve sonuçları al (İlk sayfa)
            # Elde edilen reCAPTCHA token'ı search_trademark fonksiyonuna gönderilir.
            trademark_list = await search_trademark(search_query, dynamic_params, page)

            # TODO: Eğer sayfalama uygulanacaksa, burada bir döngü kurularak 'next' parametresi
            # ve toplam sonuç sayısı kullanılarak ek sayfalar çekilmeli ve trademark_list'e eklenmeli.

        except Exception as e:
            logging.error(f"Scraping sürecinde beklenmedik bir hata oluştu: {e}")
            trademark_list = []

        finally:
            # Tarayıcıyı kapat
            if browser: # Browser objesi oluşturulduysa kapat
                await browser.close()
                logging.info("Tarayıcı kapatıldı.")
            else:
                logging.warning("Browser objesi oluşturulamadığı için kapatılamadı.")

    logging.info(f"'{search_query}' için scraping süreci tamamlandı. Çekilen sonuç sayısı: {len(trademark_list)}")
    return trademark_list


# Bu modül doğrudan çalıştırılırsa test amaçlı kullanılabilir
if __name__ == "__main__":
    # Örnek kullanım (Asenkron fonksiyonu çalıştırmak için asyncio kullanılır)
    # Dikkat: Bu testin başarılı olması, Playwright'ın görünmez reCAPTCHA'yı aşabilmesine
    # ve API'den başarılı yanıt dönebilmesine bağlıdır.
    test_query = "Vestel" # Aranacak örnek marka

    print(f"Test amaçlı scraping başlatılıyor: {test_query}")

    # asyncio.run() ile asenkron fonksiyonu çalıştırıyoruz
    results = asyncio.run(scrape_turkpatent_trademarks(test_query))

    if results:
        print(f"\nTest Sonuçları ({len(results)} adet):")
        # Çekilen marka objelerini (dictionary) kullanarak bilgileri yazdırın
        for i, trademark in enumerate(results[:10]): # İlk 10 sonucu göster
            # Sizin verdiğiniz başarılı yanıt yapısındaki anahtarları kullanıyoruz:
            marka_adi = trademark.get('markName', 'Ad Bilinmiyor')
            basvuru_no = trademark.get('applicationNo', 'Başvuru No Bilinmiyor')
            basvuru_sahibi = trademark.get('holdName', 'Sahip Bilinmiyor')
            nice_siniflari = trademark.get('niceClasses', 'Sınıf Bilinmiyor')
            durum = trademark.get('state', 'Durum Bilinmiyor')
            tescil_no = trademark.get('registrationNo', 'Tescil No Bilinmiyor') # Tescil olmayabilir

            print(f"--- Marka {i+1} ---")
            print(f"  Adı: {marka_adi}")
            print(f"  Başvuru No: {basvuru_no}")
            print(f"  Başvuru Sahibi: {basvuru_sahibi}")
            print(f"  Nice Sınıfları: {nice_siniflari}")
            print(f"  Durum: {durum}")
            print(f"  Tescil No: {tescil_no}")
            # İsterseniz diğer alanları da ekleyebilirsiniz.
            # print(f"  Ham Obje: {trademark}") # Tüm objeyi görmek isterseniz

    else:
        print("\nTest için sonuç bulunamadı veya scraping sırasında hata oluştu.")
        print("Lütfen yukarıdaki log mesajlarını kontrol edin.")
        print("Özellikle 'reCAPTCHA token alınamadı' veya 'HUMAN_CHECK_ERROR alındı' gibi hatalar arayın.")
        print("Bu hatalar, Playwright'ın reCAPTCHA'yı aşamadığı veya sitenin başka bir anti-bot önlemini tetiklediği anlamına gelir.")


    print("\nTest tamamlandı.")
