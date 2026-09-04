from scapy.all import rdpcap, IP, TCP
from scapy.layers.tls.all import TLS
from scapy.layers.tls.handshake import TLSClientHello, TLSServerHello, TLSClientKeyExchange ,TLSCertificate,TLSServerHelloDone
# tls paketlerini ve onun mesaj türlerini tanıyacak
from collections import defaultdict
# defaultdict olmayan anahtara otomatik boş liste veren sözlük 
from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
#rsa şifre çözme işlemleri için
from cryptography.hazmat.primitives.serialization import load_pem_private_key

import struct
#baytları belirli bir formatta paketlemek ve açmak için

import hmac, hashlib


paketler = rdpcap("best_game.pcap")#pcap doyasındaki tüm paketleri okuyup paketler adında listeye dolduruyor.

# Paketleri TCP bağlantısına göre grupla (kimin kiminle konuştuğuna göre)
oturumlar = defaultdict(list) #her yeni bağlantı için otomatik yeni liste oluşturacak
for p in paketler:
    if p.haslayer(TCP): #sadece tcp içeren paketlerle ilgileniyoruz
        anahtar = tuple(sorted([(p[IP].src, p[TCP].sport), (p[IP].dst, p[TCP].dport)]))
        #o paketin hangi bağlantıya ait olduğunu belirleyen kimlik üretiyoruz(kaynak ip+port ve hedef ip+port)
        #sorted kullanılmasının sebebi aynı bağlantının gidiş ve dönüş paketlerinin
        #hep aynı kimliğe düşmesini sağlamak
        oturumlar[anahtar].append(p)
        #o paketi ait oldugu oturumun listesine ekliyoruz111
        #{oturum1_kimligi: [paket1, paket2...], oturum2_kimligi: [...]}

print("Bulunan oturum sayisi:", len(oturumlar))

def tls_kayitlarini_gez(paket):
    #Bir paket, katman katman (Ethernet → IP → TCP → TLS → belki bir TLS daha...)
    #bazen birden fazla tls kaydı aynı pakette gelebilir. 
    #Fonksiyon verilen bir paketin içindeki tüm tls kayıtlarını bulup bir listeye topluyor.
    kayitlar = []
    katman = paket
    while katman:
        if katman.__class__.__name__ == "TLS":
            kayitlar.append(katman)
        katman = katman.payload if katman.payload and katman.payload.__class__.__name__ != "NoPayload" else None
    return kayitlar

def tls_prf(sir, etiket, tohum, uzunluk):
    sonuc = b""
    a = etiket + tohum
    while len(sonuc) < uzunluk:
        a = hmac.new(sir, a, hashlib.sha256).digest()
        sonuc += hmac.new(sir, a + etiket + tohum, hashlib.sha256).digest()
    return sonuc[:uzunluk]

for anahtar, oturum_paketleri in oturumlar.items():
    print("\n--- Oturum:", anahtar, "---")
    client_random = None
    server_random = None
    sifreli_pre_master = None
    ham_handshake = b""

    for p in oturum_paketleri:
        if not p.haslayer(TLS):
            continue
        for kayit in tls_kayitlarini_gez(p[TLS]):
            for mesaj in kayit.msg:
                if isinstance(mesaj, TLSClientHello):
                    client_random = struct.pack(">I", mesaj.gmt_unix_time) + bytes(mesaj.random_bytes)
                if isinstance(mesaj, TLSServerHello):
                    server_random = struct.pack(">I", mesaj.gmt_unix_time) + bytes(mesaj.random_bytes)
                if isinstance(mesaj, TLSClientKeyExchange):
                    ham = bytes(mesaj.exchkeys)
                    sifreli_pre_master = ham[2:]
                if isinstance(mesaj, (TLSClientHello, TLSServerHello, TLSCertificate, TLSServerHelloDone, TLSClientKeyExchange)):
                    ham_handshake += bytes(mesaj)

    print("client_random:", client_random.hex() if client_random else None)
    print("server_random:", server_random.hex() if server_random else None)
    print("sifreli_pre_master uzunlugu:", len(sifreli_pre_master) if sifreli_pre_master else None)

    if sifreli_pre_master is None:
        print("Bu oturumda RSA anahtar değişimi yok, atlanıyor")
        continue

    with open("server.key", "rb") as f:
        ozel_anahtar = load_pem_private_key(f.read(), password=None)

    pre_master_secret = ozel_anahtar.decrypt(sifreli_pre_master, rsa_padding.PKCS1v15())
    print("pre_master_secret uzunluğu:", len(pre_master_secret))
    print("ilk bayt (0303=TLS1.2):", pre_master_secret[:2].hex())

    session_hash = hashlib.sha256(ham_handshake).digest()
    master_secret = tls_prf(pre_master_secret, b"extended master secret", session_hash, 48)
    print("master_secret:", master_secret.hex())