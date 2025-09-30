# Asansör Üretim Takibi Uygulaması

Bu depo, asansör üretim fabrikalarında sipariş ve operasyon takibini kolaylaştırmak için hazırlanmış küçük ölçekli bir uygulama içerir. Veriler SQLite üzerinde tutulur ve ister Python kodu üzerinden ister komut satırı aracı ile yönetilebilir.

## Özellikler

- Sipariş oluşturma ve durum güncelleme (planlama, üretim, montaj, kalite kontrol, sevkiyat vb.)
- Siparişlere operasyon adımları ekleme, planlanan ve gerçekleşen süreleri takip etme
- Operasyon ilerleyişini ve notlarını kaydetme
- Kalite kontrol kayıtlarını inspector, sonuç ve açıklamalar ile birlikte saklama
- Komut satırı aracı ile sipariş listesi ve detaylı sipariş özeti görüntüleme

## Kurulum

Projenin çalışması için Python 3.11+ yeterlidir. Testleri çalıştırmak için `pytest` gereklidir.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Test bağımlılıklarını manuel kurmak isterseniz:

```bash
pip install pytest
```

## Kullanım

Veritabanını hazırlamak ve örnek bir akışı görmek için aşağıdaki adımlar izlenebilir:

```bash
python cli.py --database fabrika.db init
python cli.py --database fabrika.db create-order "Mega Asansör" "Panoramik" 2 2024-07-15
python cli.py --database fabrika.db add-step 1 "Sac Kesim" 1 --planned-hours 4.5
python cli.py --database fabrika.db update-step 1 "Sac Kesim" --status tamamlandi --actual-hours 4.0
python cli.py --database fabrika.db quality-check 1 "Ahmet" "Başarılı" --notes "Ölçümler tolerans içinde"
python cli.py --database fabrika.db summary 1
```

Her komut ilgili veritabanı dosyasını otomatik olarak oluşturur ve gerekli tablolar mevcut değilse açar.

## Testler

Pytest ile birim testlerini çalıştırabilirsiniz:

```bash
pytest
```

## Proje Yapısı

- `production_tracking/db.py`: SQLite bağlantısı ve tablo oluşturma işlemleri
- `production_tracking/service.py`: Sipariş, operasyon ve kalite kontrol kayıtlarını yöneten servis katmanı
- `cli.py`: Komut satırı arayüzü
- `tests/`: Servis katmanını test eden Pytest senaryoları
