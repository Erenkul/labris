#!/bin/bash
# Görev 8 - RPM Paketleme (msmtp + netflow2ng)
#
# Bu script, rpm-builder container'ının İÇİNDE çalıştırılmalı:
#   docker exec -it rpm-builder bash setup-rpm.sh
#
# ÖN KOŞUL: msmtp.spec ve netflow2ng.spec dosyaları önceden
# container'a kopyalanmış olmalı:
#   docker cp SPECS/msmtp.spec rpm-builder:/root/rpmbuild/SPECS/msmtp.spec
#   docker cp SPECS/netflow2ng.spec rpm-builder:/root/rpmbuild/SPECS/netflow2ng.spec
set -e

echo "=== 1) RPM klasor yapisini olustur ==="
rpmdev-setuptree

echo "=== 2) Windows satir sonlarini (CRLF) temizle ==="
sed -i 's/\r$//' ~/rpmbuild/SPECS/msmtp.spec
sed -i 's/\r$//' ~/rpmbuild/SPECS/netflow2ng.spec

echo ""
echo "############################################"
echo "# PAKET 1: msmtp"
echo "############################################"

echo "=== 3) msmtp kaynak kodunu indir ==="
spectool -g -R ~/rpmbuild/SPECS/msmtp.spec

echo "=== 4) msmtp derleme bagimliliklarini kur (gnutls-devel vb.) ==="
dnf builddep -y ~/rpmbuild/SPECS/msmtp.spec

echo "=== 5) msmtp'yi derle ve paketle ==="
rpmbuild -ba ~/rpmbuild/SPECS/msmtp.spec

echo "=== 6) msmtp'yi kur ve dogrula ==="
dnf install -y ~/rpmbuild/RPMS/x86_64/msmtp-1.8.33-1.el8.x86_64.rpm
msmtp --version

echo ""
echo "############################################"
echo "# PAKET 2: netflow2ng"
echo "############################################"

echo "=== 7) netflow2ng kaynak kodunu indir ==="
spectool -g -R ~/rpmbuild/SPECS/netflow2ng.spec

echo "=== 8) netflow2ng derleme bagimliliklarini kur (zeromq-devel, git) ==="
dnf builddep -y ~/rpmbuild/SPECS/netflow2ng.spec

echo "=== 9) netflow2ng'i derle ve paketle ==="
rpmbuild -ba ~/rpmbuild/SPECS/netflow2ng.spec

echo "=== 10) netflow2ng'i kur ve dogrula ==="
dnf install -y ~/rpmbuild/RPMS/x86_64/netflow2ng-0.2.2-1.el8.x86_64.rpm
netflow2ng --help

echo ""
echo "=== TUM PAKETLER BASARIYLA BUILD EDILDI VE DOGRULANDI ==="
echo "Uretilen .rpm dosyalari:"
find ~/rpmbuild/RPMS -name "*.rpm"