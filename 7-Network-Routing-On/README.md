# Görev 7 — Open vSwitch Üzerinden Dağıtık Konteyner Ağ Yönlendirmesi

## Ortam

- WSL2 içinde, Docker Desktop'tan bağımsız, native bir Ubuntu dağıtımı
- Docker Engine, Ubuntu içine doğrudan kurulmuş (Docker Desktop'ın WSL Integration özelliği yerine — bu özellik, konteyner PID'lerinin `/proc` üzerinden görünmesini engellediği için manuel network namespace işlemlerini imkansız kılıyordu)
- Open vSwitch (`openvswitch-switch` paketi, `ovs-vsctl` aracı)

## Faz 1 — Üç Docker Konteynerini OVS Köprüsüne Bağlama

Üç adet nginx konteyneri (`web1`, `web2`, `web3`) oluşturuldu. Her biri için:
- Bir network namespace bağlantısı (`/var/run/netns/`) kuruldu
- Bir veth çifti oluşturuldu — bir ucu konteynerin içine taşınıp `eth0` olarak adlandırıldı ve IP verildi (10.0.0.1, 10.0.0.2, 10.0.0.3), diğer ucu host tarafında bırakıldı
- Host tarafındaki veth ucu, `br0` adlı bir Open vSwitch köprüsüne port olarak eklendi (`ovs-vsctl add-port`)

**Sonuç:** Üç konteyner arasında çapraz ping testleri %0 paket kaybıyla başarılı.

## Faz 2 — HTTP İstek Hız Sınırlama (Rate Limit)

`web1` konteynerinin nginx ayarlarına (`nginx.conf`, `default.conf` — bu klasörde) şu kural eklendi:

**Test:** `web2`'den `web1`'e art arda 15 istek gönderildi. İlk birkaç istek `200 OK`, sınır aşılınca `503 Service Temporarily Unavailable` cevabı alındı.

**Kanıt:** `docs/faz2_ratelimit.pcap` — Wireshark'ta `http` filtresiyle açıldığında, `200 OK` cevaplarından `503` cevaplarına geçişi paket seviyesinde gösteriyor.

## Faz 3 — XDP ile Anahtar Kelime İçeren Paketleri Düşürme

`xdp_drop_keyword.c` (bu klasörde), gelen bir paketin TCP verisinde "gizli" kelimesini arayan ve bulursa paketi düşüren bir XDP/eBPF programı.

**Derleme:**

**Yükleme** (web1 konteynerinin kendi `eth0` arayüzüne, yani paketlerin web1'e *geldiği* uca):

**Test:**
- `curl http://10.0.0.1/` → `200` (normal istek geçiyor)
- `curl http://10.0.0.1/gizli` → `000` (hiç cevap gelmiyor — paket düşürüldü)

**Kanıt:** `docs/faz3_xdp_keyword.pcap` — Wireshark'ta `http` filtresiyle açıldığında, normal isteğin istek+cevap çifti tam görünürken, "gizli" isteğinin sadece gidiş paketi görünüyor, hiç cevap paketi yok.

## Faz 4 — Test ve Belgeleme

Wireshark testleri Faz 2 ve Faz 3'ün her ikisinde de ayrı ayrı yapıldı (yukarıdaki `docs/` klasöründeki `.pcap` dosyaları).

## Klasördeki Dosyalar

- `nginx.conf`, `default.conf` — Faz 2'nin rate limit ayarları eklenmiş nginx yapılandırma dosyaları
- `xdp_drop_keyword.c`, `xdp_drop_keyword.o` — Faz 3'ün XDP programının kaynak kodu ve derlenmiş hâli
- `docs/faz2_ratelimit.pcap` — Faz 2'nin Wireshark kanıtı
- `docs/faz3_xdp_keyword.pcap` — Faz 3'ün Wireshark kanıtı

## Karşılaşılan Sorunlar ve Çözümleri

- Docker Desktop'ın WSL Integration özelliği, konteyner PID'lerini `/proc` üzerinden görünmez kıldığı için manuel veth/namespace kurulumu imkansızdı — Docker Engine'i Ubuntu içine doğrudan kurarak çözüldü
- WSL2, terminal kapanınca (ya da konteyner durup tekrar başlayınca) veth/namespace durumunu sıfırlıyor — her seferinde OVS'teki bayat portlar silinip (`ovs-vsctl del-port`) veth'ler yeniden kuruldu
- İlk XDP derlemesinde `asm/types.h` bulunamadı hatası — mimariye özel include yolu (`-I/usr/include/x86_64-linux-gnu`) eklenerek çözüldü
- `IPPROTO_TCP` tanımsız hatası — eksik `#include <linux/in.h>` eklenerek çözüldü
- XDP programındaki döngü, içindeki `break` ifadeleri yüzünden derleyici tarafından tam açılamadı (unroll edilemedi) ve çekirdek denetleyicisi (verifier) paketi reddetti — döngü yerine sabit sayıda elle yazılmış karşılaştırma (`CHECK_AT` makrosu) kullanılarak çözüldü
- XDP programı ilk denemede `veth-web1-br` (host tarafı) üzerine takıldığı için web1'e *gelen* değil, web1'in *gönderdiği* paketleri filtreliyordu — programı web1'in kendi `eth0`'ına taşıyarak çözüldü
