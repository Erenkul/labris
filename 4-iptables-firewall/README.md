# 4 - Iptables Firewall (Network Namespaces)

## Görev Tanımı
4 network namespace (client1, client2, server, firewall) oluşturulup veth ile birbirine bağlanması; server namespace'inde örnek bir HTTP servisinin çalıştırılması; firewall namespace'i içinde stateful iptables kurallarıyla namespace'ler arası trafiğin kontrol edilmesi.

## Mimari
- **network-lab** adında, `--privileged` çalıştırılan bir Ubuntu 22.04 Docker container'ı içinde kuruldu (namespace/iptables işlemleri host yetkisi gerektirdiği için)
- 4 namespace, 4 veth çifti (client1↔firewall, client2↔firewall, server↔firewall, host↔firewall) ile birbirine bağlandı
- IP planı: client1 `192.0.2.0/26`, client2 `192.0.2.64/26`, server `192.0.2.128/26`, host-firewall `192.0.2.192/26` (görev PDF'inde verilen bloklar)
- Firewall, varsayılan `DROP` politikasıyla, sadece açıkça izin verilen trafiği geçiriyor (stateful: `ESTABLISHED,RELATED` bağlantılar otomatik kabul ediliyor)

## Kullanılan Teknolojiler
Linux network namespaces, veth, iptables (filter + nat table), Docker, Ubuntu 22.04

## Kurallar
- a) Client1 → server ping ✅
- b) Client2 → server HTTP ✅
- c) Client2 → firewall ping ✅
- d) Client1 → firewall ping (engelli, varsayılan DROP ile) ✅
- e) Client/server ağları → internet (host üzerinden NAT ile) ✅

## Çalıştırma
\`\`\`
docker build -t network-lab .
docker run -dit --privileged --name network-lab network-lab
docker exec -it network-lab bash setup-network.sh
\`\`\`

## Karşılaşılan Sorunlar ve Çözümler
- Okul ağında Docker Hub'dan image indirirken TLS hatası alındı; mobil hotspot ile çözüldü.
- Firewall namespace'inde `net.ipv4.ip_forward` varsayılan olarak kapalı gelebiliyor (test ortamına göre değişiyor); bu yüzden script'e açıkça `sysctl -w net.ipv4.ip_forward=1` eklendi, hem firewall hem host için.
- NAT (MASQUERADE) kuralı hem host hem firewall seviyesinde ayrı ayrı gerekiyor, çünkü paket internete çıkarken iki ayrı router'dan (firewall + host) geçiyor.



4-Create an Iptables Firewall
Tasks
Notes
Topology
Tasks
1. Create 4 network namespaces.
2. Namespaces are client1, client2, server, firewall
3. Create veth for all namespaces and your host-to-firewall for network communication.
4. Serve sample http service inside the server namespace
5. Create iptablesrulesinside the firewall namespace and controltraffic between the namespaces.
6. Rules
a. Client1 can ping to server
b. Client2 can accessto server for http
c. Client2 can ping to firewall
d. Client1 doesn't have ping permission to firewall
e. Client and server networks are can be accessto the internet from firewall namespace via your host machine.
Notes
Client1 subnetwork is 192.0.2.0/26
Client2 subnetwork is 192.0.2.64/26
Serversubnetwork is 192.0.2.128/26
Host-To-Firewall Subnetwork is 192.0.2.192/26
Firewallshould be a stateful.
