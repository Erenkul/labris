# 9 - Django'yu Çoklu Port'ta Çalıştırma

## Görev Tanımı
MVC (Django'da MTV) mimarisine uygun bir Django sitesi kurulması; uygulamanın 80 (admin panel) ve 85 (kullanıcı panel) portlarından servis edilmesi; MySQL kullanımı; normal kullanıcının admin paneline erişiminin engellenmesi.

## Mimari
- **Docker Compose** ile 3 servis: `db` (MySQL 8.0), `admin-panel` (port 80), `user-panel` (port 85)
- Tek bir Django proje kod tabanı, `DJANGO_URLCONF` ortam değişkeniyle her servis için farklı `urls.py` seçiliyor (`config/urls_admin.py` / `config/urls_user.py`)
- Admin panel için Django'nun hazır `django.contrib.admin` uygulaması kullanıldı — `is_staff=True` olmayan kullanıcılar otomatik olarak reddediliyor
- `panel` app'i içinde `Duyuru` modeli; admin panelden eklenen veriler, kullanıcı panelinde (MTV: Model → View → Template) listeleniyor

## Kullanılan Teknolojiler
Python, Django 5.2, MySQL 8.0, Docker, Docker Compose

## Çalıştırma
\`\`\`
docker build -t django-multiport .
docker-compose up -d db
docker-compose run --rm admin-panel python manage.py migrate
docker-compose run --rm admin-panel python manage.py createsuperuser
docker-compose up -d admin-panel user-panel
\`\`\`
- Admin panel: http://127.0.0.1/admin/
- Kullanıcı panel: http://127.0.0.1:85/

## Karşılaşılan Sorunlar ve Çözümler
- Okul/kurum ağında Docker Hub image indirirken (`mysql:8.0`) sürekli `tls: handshake failure` hatası alındı; mobil hotspot üzerinden indirilerek çözüldü.
- `settings.py`'de `ROOT_URLCONF` ortam değişkeni `DJANGOG_URLCONF` (fazladan bir "G") olarak yazılmıştı; bu yüzden panel her zaman varsayılan `urls.py`'ye düşüyordu. Değişken adı düzeltilerek çözüldü.
- `panel/views.py` içinde `from models import Duyuru` (başında nokta eksik) `ModuleNotFoundError` hatası verdi; `from .models import Duyuru` olarak düzeltildi.
- Template'e gönderilen context anahtarı (`duyuru`) ile template içindeki döngü değişkeni (`duyurular`) uyuşmuyordu; anahtar `duyurular` olarak düzeltildi.

## Doğrulama
Normal (`is_staff=False`) bir kullanıcı ile `/admin/` girişi denendiğinde Django şu hatayı veriyor: *"Please enter the correct username and password for a staff account."* — görevin istediği erişim kısıtlaması doğrulandı.