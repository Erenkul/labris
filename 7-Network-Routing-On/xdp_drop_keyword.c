#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/in.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#define KEYWORD_LEN 5

SEC("xdp")
int xdp_drop_keyword_prog(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;

    if (ip->protocol != IPPROTO_TCP)
        return XDP_PASS;

    struct tcphdr *tcp = (void *)ip + (ip->ihl * 4);
    if ((void *)(tcp + 1) > data_end)
        return XDP_PASS;

    unsigned char *payload = (unsigned char *)tcp + (tcp->doff * 4);

#define CHECK_AT(off) \
    (payload + (off) + KEYWORD_LEN <= (unsigned char *)data_end && \
     payload[(off)+0] == 'g' && payload[(off)+1] == 'i' && \
     payload[(off)+2] == 'z' && payload[(off)+3] == 'l' && \
     payload[(off)+4] == 'i')

    if (CHECK_AT(0)  || CHECK_AT(1)  || CHECK_AT(2)  || CHECK_AT(3)  || CHECK_AT(4)  ||
        CHECK_AT(5)  || CHECK_AT(6)  || CHECK_AT(7)  || CHECK_AT(8)  || CHECK_AT(9)  ||
        CHECK_AT(10) || CHECK_AT(11) || CHECK_AT(12) || CHECK_AT(13) || CHECK_AT(14) ||
        CHECK_AT(15) || CHECK_AT(16) || CHECK_AT(17) || CHECK_AT(18) || CHECK_AT(19))
        return XDP_DROP;

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
