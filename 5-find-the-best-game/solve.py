#"Diffie-Hellman problemi"


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

from scapy.layers.tls.record import TLSApplicationData
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

import hmac, hashlib


paketler = rdpcap("best_game.pcap")#pcap doyasındaki tüm paketleri okuyup paketler adında listeye dolduruyor.

# Paketleri TCP bağlantısına göre grupla (kimin kiminle konuştuğuna göre)
oturumlar = defaultdict(list) #her yeni bağlantı için otomatik yeni liste oluşturacak
"""{
    oturum_1: [paket1, paket2, paket3],
    oturum_2: [paket4, paket5]
}
bu da şuna geliyor

anahtar = tuple(sorted([
    (p[IP].src, p[TCP].sport),
    (p[IP].dst, p[TCP].dport)
]))
"""
for p in paketler:
    if p.haslayer(TCP): #sadece tcp içeren paketlerle ilgileniyoruz
        anahtar = tuple(sorted([(p[IP].src, p[TCP].sport),
                              (p[IP].dst, p[TCP].dport)])
                        )
        #o paketin hangi bağlantıya ait olduğunu belirleyen kimlik üretiyoruz(kaynak ip+port ve hedef ip+port)
        #sorted kullanılmasının sebebi aynı bağlantının gidiş ve dönüş paketlerinin
        #hep aynı kimliğe düşmesini sağlamak
        oturumlar[anahtar].append(p)
        #o paketi ait oldugu oturumun listesine ekliyoruz111
        #{oturum1_kimligi: [paket1, paket2...], oturum2_kimligi: [...]}

print("Bulunan oturum sayisi:", len(oturumlar))

def tls_kayitlarini_gez(paket):
    #Bir paket, katman katman (Ethernet → IP → TCP → TLS → belki bir TLS daha...)
    #Bir tcp paketinde birden fazla tls kaydı olabilir fonksiyon scapy katmanları içinde ilerleyerek bütün tls katmanlarını topluyor
    #Fonksiyon verilen bir paketin içindeki tüm tls kayıtlarını bulup bir listeye topluyor.
    kayitlar = []
    katman = paket
    while katman:
        if katman.__class__.__name__ == "TLS":
            kayitlar.append(katman)
        katman = katman.payload if katman.payload and katman.payload.__class__.__name__ != "NoPayload" else None
    return kayitlar
#bir tcp paketi şunlları birlikte taşıyabilir: serverhello,certificate,serverhellodone



def tls_prf(sir, etiket, tohum, uzunluk):
    """bu fonksiyon master secret, istemci şifreleme anahtarı, sunucu şifreleme anahtarı,HMAC anahtarları gibi
        sir: initial value, 
        etiket: hangi anahtarın üretileceğini belirten yazı
        tohum: random ve handshake summary
        uzunluk: kaç byte üretileceği
                                                    ----->> sha256 her seferinde 32 byte ürettiği için while
                                                    döngüsünde oraya kadar progress.
    """
    sonuc = b""
    a = etiket + tohum
    while len(sonuc) < uzunluk:
        a = hmac.new(sir, a, hashlib.sha256).digest()
        sonuc += hmac.new(sir, a + etiket + tohum, hashlib.sha256).digest()
    return sonuc[:uzunluk]

for anahtar, oturum_paketleri in oturumlar.items():
    print("\n--- Oturum:", anahtar, "---")
    client_random = None #istemcinin gönderdiği 32 byte lık rastgele değer
    server_random = None #sunucunun gönderdiği 32 bytlık rastgele değer
    sifreli_pre_master = None #RSA ile şiflreme
    ham_handshake = b"" #handshake mesajlarının ham bytle ları
    uygulama_verileri=[]

    #ClientHello ve ServerHello tamamen gizli mesajlar değildir. Tarafların TLS sürümü ve şifreleme yöntemi üzerinde anlaşmasını sağlar.

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
                if isinstance(mesaj, TLSApplicationData):
                    yon = "istemciden" if p[IP].src == anahtar[0][0] else "sunucudan"
                    uygulama_verileri.append((yon, bytes(mesaj.data)))

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

    key_block = tls_prf(master_secret, b"key expansion", server_random + client_random, 72)
    client_mac_key = key_block[0:20]
    server_mac_key = key_block[20:40]
    client_key = key_block[40:56]
    server_key = key_block[56:72]
    print("client_key:", client_key.hex())
    print("server_key:", server_key.hex())

    for yon, kayit in uygulama_verileri:
        iv = kayit[:16]
        sifreli_veri = kayit[16:]
        kullanilacak_anahtar = client_key if yon == "istemciden" else server_key

        cipher = Cipher(algorithms.AES(kullanilacak_anahtar), modes.CBC(iv))
        cozucu = cipher.decryptor()
        duz_veri = cozucu.update(sifreli_veri) + cozucu.finalize()

        dolgu_uzunlugu = duz_veri[-1]
        gercek_mesaj = duz_veri[:-1 - dolgu_uzunlugu - 20]

        print(f"\n--- {yon} ---")
        print(gercek_mesaj.decode(errors="replace"))

