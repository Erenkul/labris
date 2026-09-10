#!/bin/bash
set -e

echo "1) Docker servisini baslat..."
sudo service docker start

echo "2) Konteynerleri baslat (yoksa olustur, varsa baslat)..."
for c in web1 web2 web3; do
  if [ "$(docker ps -aq -f name=^${c}$)" ]; then
    docker start $c
  else
    docker run -d --name $c --network none nginx
  fi
done

echo "3) OVS koprusunu olustur (yoksa)..."
sudo ovs-vsctl --may-exist add-br br0

echo "4) Bayat portlari temizle..."
for c in web1 web2 web3; do
  sudo ovs-vsctl --if-exists del-port br0 veth-$c-br
done

echo "5) Namespace baglantilarini ve veth kablolarini yeniden kur..."
i=1
for c in web1 web2 web3; do
  pid=$(docker inspect -f '{{.State.Pid}}' $c)
  sudo mkdir -p /var/run/netns
  sudo ln -sfT /proc/$pid/ns/net /var/run/netns/$c

  sudo ip link add veth-$c type veth peer name veth-$c-br
  sudo ip link set veth-$c netns $c
  sudo ip netns exec $c ip link set veth-$c name eth0
  sudo ip netns exec $c ip addr add 10.0.0.$i/24 dev eth0
  sudo ip netns exec $c ip link set eth0 up
  sudo ip netns exec $c ip link set lo up
  sudo ip link set veth-$c-br up
  sudo ovs-vsctl add-port br0 veth-$c-br
  i=$((i+1))
done

echo "6) web1'e rate limit ayarlarini uygula..."
docker cp nginx.conf web1:/etc/nginx/nginx.conf
docker cp default.conf web1:/etc/nginx/conf.d/default.conf
docker exec web1 nginx -t
docker exec web1 nginx -s reload

echo "7) XDP programini web1'in eth0'ina yukle..."
sudo ip netns exec web1 ip link set dev eth0 xdp obj xdp_drop_keyword.o sec xdp

echo "Kurulum tamamlandi."
