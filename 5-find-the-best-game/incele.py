from scapy.all import rdpcap, TCP
from scapy.layers.tls.all import TLS
from scapy.layers.tls.handshake import TLSClientHello, TLSServerHello

for dosya in ["best_game.pcap", "best_game_tls1_3.pcap"]:
    print(f"=== {dosya} ===")
    paketler = rdpcap(dosya)
    print("Paket sayisi:", len(paketler))

    for p in paketler:
        if p.haslayer(TLS):
            tls = p[TLS]
            if tls.haslayer(TLSClientHello):
                ch = tls[TLSClientHello]
                print("ClientHello -> versiyon:", hex(ch.version))
            if tls.haslayer(TLSServerHello):
                sh = tls[TLSServerHello]
                print("ServerHello -> versiyon:", hex(sh.version), "cipher:", hex(sh.cipher))
    print()