#!/bin/bash
# Görev 4 - Iptables Firewall
# Bu script, network-lab container'ının İÇİNDE çalıştırılmalı:
#   docker exec -it network-lab bash setup-network.sh
set -e  # herhangi bir komut hata verirse script dursun

echo "=== 1) Namespace'leri oluştur ==="
ip netns add client1
ip netns add client2
ip netns add server
ip netns add firewall

echo "=== 2) veth çiftlerini oluştur ==="
ip link add fw-c1 type veth peer name c1-fw
ip link add fw-c2 type veth peer name c2-fw
ip link add fw-sv type veth peer name sv-fw
ip link add fw-h type veth peer name h-fw

echo "=== 3) Uçları ilgili namespace'lere taşı ==="
ip link set c1-fw netns client1
ip link set fw-c1 netns firewall
ip link set c2-fw netns client2
ip link set fw-c2 netns firewall
ip link set sv-fw netns server
ip link set fw-sv netns firewall
ip link set fw-h netns firewall
# h-fw host'ta (ana namespace'te) kalıyor

echo "=== 4) IP adreslerini ata ==="
ip netns exec client1 ip addr add 192.0.2.2/26 dev c1-fw
ip netns exec client2 ip addr add 192.0.2.66/26 dev c2-fw
ip netns exec server  ip addr add 192.0.2.130/26 dev sv-fw
ip netns exec firewall ip addr add 192.0.2.1/26 dev fw-c1
ip netns exec firewall ip addr add 192.0.2.65/26 dev fw-c2
ip netns exec firewall ip addr add 192.0.2.129/26 dev fw-sv
ip netns exec firewall ip addr add 192.0.2.194/26 dev fw-h
ip addr add 192.0.2.193/26 dev h-fw

echo "=== 5) Arayüzleri (ve loopback'leri) aktif et ==="
ip netns exec client1 ip link set c1-fw up
ip netns exec client1 ip link set lo up
ip netns exec client2 ip link set c2-fw up
ip netns exec client2 ip link set lo up
ip netns exec server  ip link set sv-fw up
ip netns exec server  ip link set lo up
ip netns exec firewall ip link set fw-c1 up
ip netns exec firewall ip link set fw-c2 up
ip netns exec firewall ip link set fw-sv up
ip netns exec firewall ip link set fw-h up
ip netns exec firewall ip link set lo up
ip link set h-fw up

echo "=== 6) Varsayılan rotalar ==="
ip netns exec client1 ip route add default via 192.0.2.1
ip netns exec client2 ip route add default via 192.0.2.65
ip netns exec server  ip route add default via 192.0.2.129
ip netns exec firewall ip route add default via 192.0.2.193

echo "=== 7) Server'da örnek HTTP servisi başlat ==="
mkdir -p /tmp/webroot
echo 'Merhaba, server namespace calisiyor' > /tmp/webroot/index.html
setsid ip netns exec server python3 -m http.server 80 --bind 192.0.2.130 --directory /tmp/webroot < /dev/null > /tmp/http_server.log 2>&1 &
disown
sleep 1

echo "=== 8) Firewall: varsayılan politika DROP ==="
ip netns exec firewall iptables -P INPUT DROP
ip netns exec firewall iptables -P FORWARD DROP

echo "=== 9a) Firewall: kendi kernel'inde ip_forward'i ac ==="
ip netns exec firewall sysctl -w net.ipv4.ip_forward=1

echo "=== 9b) Firewall: loopback + stateful (ESTABLISHED,RELATED) ==="
ip netns exec firewall iptables -A INPUT -i lo -j ACCEPT
ip netns exec firewall iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
ip netns exec firewall iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

echo "=== 10) Kural a, b, c (d icin ek kural gerekmiyor, varsayilan DROP hallediyor) ==="
# a) Client1 -> server ping
ip netns exec firewall iptables -A FORWARD -s 192.0.2.0/26 -d 192.0.2.128/26 -p icmp --icmp-type echo-request -j ACCEPT
# b) Client2 -> server http
ip netns exec firewall iptables -A FORWARD -s 192.0.2.64/26 -d 192.0.2.128/26 -p tcp --dport 80 -j ACCEPT
# c) Client2 -> firewall ping
ip netns exec firewall iptables -A INPUT -s 192.0.2.64/26 -p icmp --icmp-type echo-request -j ACCEPT

echo "=== 11) Kural e: internet erisimi (NAT) - host tarafi ==="
iptables -A FORWARD -i h-fw -j ACCEPT
iptables -A FORWARD -o h-fw -j ACCEPT
sysctl -w net.ipv4.ip_forward=1
iptables -t nat -A POSTROUTING -s 192.0.2.0/24 -o eth0 -j MASQUERADE

echo "=== 12) Kural e: internet erisimi (NAT) - firewall tarafi ==="
ip netns exec firewall iptables -A FORWARD -s 192.0.2.0/26 -o fw-h -j ACCEPT
ip netns exec firewall iptables -A FORWARD -s 192.0.2.64/26 -o fw-h -j ACCEPT
ip netns exec firewall iptables -A FORWARD -s 192.0.2.128/26 -o fw-h -j ACCEPT
ip netns exec firewall iptables -t nat -A POSTROUTING -s 192.0.2.0/24 -o fw-h -j MASQUERADE

echo "=== KURULUM TAMAMLANDI ==="