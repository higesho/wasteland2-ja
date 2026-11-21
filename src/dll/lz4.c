/* LZ4 ブロック形式をほどく（大きさを書かない形式。python の lz4.block.compress(store_size=False)） */
int lz4_decompress(const unsigned char *src, int srclen, unsigned char *dst, int dstlen)
{
    const unsigned char *ip = src, *iend = src + srclen;
    unsigned char *op = dst, *oend = dst + dstlen;
    while (ip < iend) {
        unsigned tok = *ip++;
        unsigned lit = tok >> 4;
        if (lit == 15) { unsigned char b; do { if (ip >= iend) return -1; b = *ip++; lit += b; } while (b == 255); }
        if (ip + lit > iend || op + lit > oend) return -1;
        for (unsigned i = 0; i < lit; i++) *op++ = *ip++;
        if (ip >= iend) break;
        if (ip + 2 > iend) return -1;
        unsigned off = ip[0] | (ip[1] << 8); ip += 2;
        if (off == 0 || op - dst < (int)off) return -1;
        unsigned ml = tok & 15;
        if (ml == 15) { unsigned char b; do { if (ip >= iend) return -1; b = *ip++; ml += b; } while (b == 255); }
        ml += 4;
        if (op + ml > oend) return -1;
        const unsigned char *m = op - off;
        for (unsigned i = 0; i < ml; i++) *op++ = *m++;
    }
    return (int)(op - dst);
}
