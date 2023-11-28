import numpy as np
from struct import unpack

"""
FFC0                SOF0    Baseline DCT
FFC4                DHT     Define Huffman table(s)
FFD8                SOI     Start of image
FFD9                EOI     End of image
FFDA                SOS     Start of scan
FFDB                DQT     Define quantization table(s)
FFDC                DNL     Define number of lines
FFDD                DRI     Define restart interval
FFDE                DHP     Define hierarchical progression
FFDF                EXP     Expand reference component(s)
FFE0 through FFEF   APPn    Reserved for application segments
FFF0 through FFFD   JPGn    Reserved for JPEG extensions
FFFE                COM     Comment
"""


class JPEG_decoder:
    def __init__(self, jpg):
        with open(jpg, "rb") as f:
            self.jpg = f.read()
        self.quant = {}
        self.DC_huff = []
        self.AC_huff = []
        self.frame = []
        print(self.jpg)

    def decode(self):
        now = 0
        while True:
            if hex(self.jpg[now]) == "0xff":
                # SOI
                if hex(self.jpg[now + 1]) == "0xd8":
                    print("Start of image")
                    now += 2

                # EOI
                elif hex(self.jpg[now + 1]) == "0xd9":
                    print("End of image")
                    return

                # SOS
                elif hex(self.jpg[now + 1]) == "0xda":
                    self.decode_scan(self.jpg[now + 2 : -2])
                    now = len(self.jpg) - 2

                else:
                    length = self.jpg[now + 2] * 256 + self.jpg[now + 3]
                    # APP0
                    if hex(self.jpg[now + 1]) == "0xe0":
                        pass

                    # quant table
                    elif hex(self.jpg[now + 1]) == "0xdb":
                        self.def_quant_table(self.jpg[now + 4 : now + length + 2])

                    # SOF0
                    elif hex(self.jpg[now + 1]) == "0xc0":
                        self.dec_frame_head(self.jpg[now + 4 : now + length + 2])

                    # DHT
                    elif hex(self.jpg[now + 1]) == "0xc4":
                        self.def_huff_table(self.jpg[now + 4 : now + length + 2])


                    now += length + 2

    def def_quant_table(self, data):
        quant_id = data[0]
        self.quant[quant_id] = np.array(list(data[1:])).reshape((8, 8))
        # print(f"quant table {quant_id}")
        # print(self.quant[quant_id])
        return

    def dec_frame_head(self, data):
        precision = data[0]
        self.height = data[1] * 256 + data[2]
        self.width = data[3] * 256 + data[4]
        img_num = data[5]
        now = 6
        # print(precision, self.height, self.width, img_num)
        for _ in range(img_num):
            img_id = data[now]
            sf_h = data[now + 1] // 16
            sf_v = data[now + 1] % 16
            quant = data[now + 2]
            self.frame.append((img_id, sf_h, sf_v, quant))
            now += 3
        return

    def def_huff_table(self, data):
        print(len(data))
        table_class = data[0] // 16
        dest = data[0] % 16
        huffsize = []
        huffcode = []
        # now = 17
        # for i in range(len(data[1:17])):
        #     for j in range(data[1 + i]):
        #         length.append(i)
        #         elements.append(data[now])
        #         now += 1
        # print(data[1:17], length, elements)

        j = 1
        for i in range(1, 17):
            while True:
                if j > data[i]:
                    j = 1
                    break
                else:
                    huffsize.append(i)
                    j += 1
        huffsize.append(0)
        k, code = 0, 0
        si = huffsize[0]
        while True:
            huffcode.append(bin(code)[2:])
            k += 1
            code += 1
            while huffsize[k] == si:
                huffcode.append(bin(code)[2:])
                k += 1
                code += 1
            if huffsize[k] == 0:
                break
            else:
                code = code << 1
                si += 1
                while huffsize[k] != si:
                    code = code << 1
                    si += 1
        for i in range(len(huffcode)):
            if huffsize[i] > len(huffcode[i]):
                huffcode[i] = (huffsize[i] - len(huffcode[i])) * "0" + huffcode[i]
        # print(huffcode)
        dic = dict(zip(huffcode, data[17:]))
        print(dic)
        if table_class == 0:
            self.DC_huff.append(dic)
        else:
            self.AC_huff.append(dic)
        return

    def decode_scan(self, data):
        pass


if __name__ == "__main__":
    decoder = JPEG_decoder("./images/monalisa.jpg")
    decoder.decode()
    # print(hex(255) == "0xff")
