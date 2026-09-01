# 8 - RPM Paketleme (msmtp + netflow2ng)

## Görev Tanımı
Verilen iki açık kaynak projeyi (msmtp, netflow2ng) kaynak kodundan CentOS8 için RPM paketi haline getirmek; paketlerin `dnf` ile, tüm bağımlılıklarıyla birlikte kurulabilir olması bekleniyor.

## Mimari
- Tek bir CentOS8 Docker container'ı (`rpm-builder`) içinde, iki bağımsız `.spec` dosyası ile iki paket üretildi
- **msmtp** — C ile yazılmış, autotools (`./configure && make`) tabanlı klasik bir proje
- **netflow2ng** — Go ile yazılmış, kendi `Makefile`'ı olan, protobuf kod üretimi gerektiren daha karmaşık bir proje

## Kullanılan Teknolojiler
`rpmbuild`, `rpmdevtools`, `dnf`/EPEL, GnuTLS, Go 1.26.2, Protocol Buffers (`protoc` + `protoc-gen-go`), ZeroMQ

## Çalıştırma
docker build -t rpm-builder .
docker run -dit --name rpm-builder rpm-builder
docker cp SPECS/msmtp.spec rpm-builder:/root/rpmbuild/SPECS/msmtp.spec
docker cp SPECS/netflow2ng.spec rpm-builder:/root/rpmbuild/SPECS/netflow2ng.spec
docker exec -it rpm-builder bash setup-rpm.sh


## Karşılaşılan Sorunlar ve Çözümler

### msmtp
- `Source0` URL'i yanlıştı (`/download/` yerine `/releases/` olmalıydı) — düzeltildi
- Windows'ta düzenlenen `.spec` dosyasındaki gizli CRLF (`\r`) karakterleri, `make -j` komutunun argümanını bozdu — `sed -i 's/\r$//'` ile temizlendi
- Kaynak kodun `base64.c`/`base64.h` dosyaları `bool` tipini `<stdbool.h>` import etmeden kullanıyordu — `CFLAGS`'a `-include stdbool.h` eklenerek çözüldü
- `%files` listesi eksikti (`msmtpd`, çeviri dosyaları, info sayfası listelenmemişti) — `%find_lang` makrosu ve eksik dosya yolları eklenerek tamamlandı

### netflow2ng
- CentOS8'in `dnf` ile verdiği Go sürümü (1.16) çok eskiydi, projenin `go.mod`'undaki yeni sürüm formatını (`go 1.23.0`) okuyamıyordu — Go, resmi kaynağından (go.dev) elle kuruldu
- `zeromq-devel` CentOS8'in varsayılan depolarında yoktu — EPEL deposu etkinleştirildi
- `protoc` (Protocol Buffers derleyicisi) kurulu değildi — GitHub'dan hazır binary indirildi
- `protoc-gen-go` (protoc'un Go kod üretme eklentisi) eksikti — `go install` ile kuruldu
- Derlenen dosyanın adı (`netflow2ng-0.2.2`) `.spec`'in beklediğinden (`netflow2ng`) farklıydı — `%install` bölümü düzeltildi
- Go binary'leri standart C debug formatını kullanmadığı için RPM'in otomatik debug paketleme adımı boş bir paket üretmeye çalıştı — `%global debug_package %{nil}` eklenerek devre dışı bırakıldı

## Doğrulama
İki paket de `dnf install` ile kuruldu ve çalıştırıldı:
- `msmtp --version` → sürüm bilgisini doğru bastı
- `netflow2ng --help` → yardım metnini doğru bastı