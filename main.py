import sys
import numpy as np
import matplotlib.pyplot as plt

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
    def __init__(self, jpg, file_name):
        with open(jpg, "rb") as f:
            self.jpg = f.read()
        self.file_name = file_name[:-4]
        self.quant = {}
        self.DC_huff = []
        self.AC_huff = []
        self.frame = []
        self.dct = np.zeros((8, 8))
        for k in range(8):
            for n in range(8):
                self.dct[k][n] = np.sqrt(1/8)*np.cos(np.pi*k*(1/2+n)/8)
                if k != 0:
                    self.dct[k][n] *= np.sqrt(2)
        self.idct = np.kron(self.dct.transpose(), self.dct.transpose())
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
                        print(length)
                        self.def_quant_table(self.jpg[now + 4 : now + length + 2], length)

                    # SOF0
                    elif hex(self.jpg[now + 1]) == "0xc0":
                        self.dec_frame_head(self.jpg[now + 4 : now + length + 2])

                    # DHT
                    elif hex(self.jpg[now + 1]) == "0xc4":
                        self.def_huff_table(self.jpg[now + 4 : now + length + 2], length)

                    now += length + 2

    def def_quant_table(self, data, length):
        length -= 2
        while length > 0:
            quant_id = data[0]
            # self.quant[quant_id] = np.array(list(data[1:])).reshape((8, 8))
            self.quant[quant_id] = np.zeros((8, 8), dtype=int)
            for i in range(64):
                self.quant[quant_id] = self.fill_matrix(self.quant[quant_id], i, data[1+i])

            print(f"quant table {quant_id}")
            print(self.quant[quant_id])
            length -= 65
            data = data[65:]
        return

    def dec_frame_head(self, data):
        precision = data[0]
        self.height = data[1] * 256 + data[2]
        self.width = data[3] * 256 + data[4]
        img_num = data[5]
        now = 6
        print(precision, self.height, self.width, img_num)
        for _ in range(img_num):
            img_id = data[now]
            sf_h = data[now + 1] // 16
            sf_v = data[now + 1] % 16
            quant = data[now + 2]
            self.frame.append((img_id, sf_h, sf_v, quant))
            now += 3
        print(self.frame)
        return

    def def_huff_table(self, data, length):
        # print(len(data))
        length -= 2
        while length > 0:
            table_class = data[0] // 16
            dest = data[0] % 16
            huffsize = []
            huffcode = []

            j = 1
            for i in range(1, 17):
                while True:
                    if j > data[i]:
                        j = 1
                        break
                    else:
                        huffsize.append(i)
                        j += 1
            length -= 17
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
            length -= len(huffcode)
            dic = dict(zip(huffcode, data[17:]))
            print(dic)
            if table_class == 0:
                self.DC_huff.append(dic)
            else:
                self.AC_huff.append(dic)
            data = data[17+len(huffcode):]
        return

    def decode_scan(self, data):
        length = data[0] * 256 + data[1] - 3
        ns = data[2]
        self.tab_tab = []
        now = 4
        for _ in range(ns):
            self.tab_tab.append([data[now] // 16, data[now] % 16])
            now += 2
        print(self.tab_tab)
        now += 2
        self.decode_image(data[now:])

    def decode_image(self, data):
        # print(bin(data[0])[2:], bin(data[1])[2:], bin(data[2])[2:])
        # [0, -24, -33]
        new_data = []
        i = 0
        while i < len(data) - 1:
            if data[i] == 255:
                if data[i+1] == 0:
                    new_data.append(data[i])
                    i += 2
                    continue
            new_data.append(data[i])
            i = i + 1
        data = new_data
                    
        # print("".join(list(map(lambda x: "0"*(8-len(bin(x)[2:])) + bin(x)[2:], data))))
        if self.frame[0][1] == 2 and self.frame[0][2] == 2:
            mcu_h_num = int(np.ceil(self.height/16))
            mcu_w_num = int(np.ceil(self.width/16))
            image = np.zeros((mcu_h_num*16, mcu_w_num*16, 3))
            img = np.zeros((mcu_h_num*16, mcu_w_num*16, 3))
        elif self.frame[0][1] == 2 and self.frame[0][2] == 1:
            mcu_h_num = int(np.ceil(self.height/8))
            mcu_w_num = int(np.ceil(self.width/16))
            image = np.zeros((mcu_h_num*8, mcu_w_num*16, 3))
            img = np.zeros((mcu_h_num*8, mcu_w_num*16, 3))
        count = 0
        global st
        st = Stream(data)
        dc_coef = [0, 0, 0]
        
        for h in range(mcu_h_num):
            for w in range(mcu_w_num):
                print(count)
                mcu_component = []
                if self.frame[0][1] == 2 and self.frame[0][2] == 2:
                    for i in range(6):
                        if i < 4:
                            idx = 0
                        elif i == 4:
                            idx = 1
                        elif i == 5:
                            idx = 2
                        decoded_matrix, dc_coef[idx] = self.decode_matrix(idx, dc_coef[idx])
                        print(decoded_matrix)
                        dequanted_matrix = np.multiply(decoded_matrix, self.quant[self.frame[idx][-1]])
                        # print(dequanted_matrix)
                        idcted_matrix = (self.idct @ dequanted_matrix.flatten()).reshape((8, 8)) + 128
                        # print(idcted_matrix)
                        mcu_component.append(idcted_matrix)
                    # print(st.GetRemain())
                    h_i, w_i = h*16, w*16
                    image[h_i:h_i+8, w_i:w_i+8, 0] = mcu_component[0]
                    image[h_i:h_i+8, w_i+8:w_i+16, 0] = mcu_component[1]
                    image[h_i+8:h_i+16, w_i:w_i+8, 0] = mcu_component[2]
                    image[h_i+8:h_i+16, w_i+8:w_i+16, 0] = mcu_component[3]
                    image[h_i:h_i+16, w_i:w_i+16, 1] = self.resize(mcu_component[4])
                    image[h_i:h_i+16, w_i:w_i+16, 2] = self.resize(mcu_component[5])
                    count += 1
    
                elif self.frame[0][1] == 2 and self.frame[0][2] == 1:
                    for i in range(4):
                        if i < 2:
                            idx = 0
                        elif i == 2:
                            idx = 1
                        elif i == 3:
                            idx = 2
                        decoded_matrix, dc_coef[idx] = self.decode_matrix(idx, dc_coef[idx])
                        print(decoded_matrix)
                        dequanted_matrix = np.multiply(decoded_matrix, self.quant[self.frame[idx][-1]])
                        # print(dequanted_matrix)
                        idcted_matrix = (self.idct @ dequanted_matrix.flatten()).reshape((8, 8)) + 128
                        # print(idcted_matrix)
                        mcu_component.append(idcted_matrix)
                    # print(st.GetRemain())
                    h_i, w_i = h*8, w*16
                    image[h_i:h_i+8, w_i:w_i+8, 0] = mcu_component[0]
                    image[h_i:h_i+8, w_i+8:w_i+16, 0] = mcu_component[1]
                    image[h_i:h_i+8, w_i:w_i+16, 1] = self.resize(mcu_component[2], 2)
                    image[h_i:h_i+8, w_i:w_i+16, 2] = self.resize(mcu_component[3], 2)
                    count += 1

        img[:, :, 0] = image[:, :, 0] + (image[:, :, 2] - 128)*1.402
        img[:, :, 1] = image[:, :, 0] - 0.34414*(image[:, :, 1] - 128) - 0.71414 * (image[:, :, 2] - 128)
        img[:, :, 2] = image[:, :, 0] + 1.772 * (image[:, :, 1] - 128)
        img = img[:self.height, :self.width, :]
        img = np.clip(img, 0, 255)
        plt.imsave(f"./{self.file_name}.bmp", img.astype(np.uint8))
        
    def resize(self, matrix, resize_type=1):
        if resize_type == 1:
            new_matrix = np.zeros((16, 16))
            for i in range(16):
                for j in range(16):
                    new_matrix[i][j] = matrix[i//2][j//2]
        else:
            new_matrix = np.zeros((8, 16))
            for i in range(8):
                for j in range(16):
                    new_matrix[i][j] = matrix[i][j//2]
        return new_matrix

    def decode_matrix(self, idx, dc_coef):
        print(idx)
        matrix = np.zeros((8, 8), dtype=int)
        dc_idx, ac_idx = self.tab_tab[idx]
        print(dc_idx, ac_idx)
        now_word = ""
        while now_word not in self.DC_huff[dc_idx]:
            now_word += st.GetBit()
        flw_bit_n = self.DC_huff[self.tab_tab[idx][0]][now_word]
        if flw_bit_n == 0:
            coef = 0
        else:
            flw_bit = "".join([st.GetBit() for _ in range(flw_bit_n)])
            coef = self.magnitude(flw_bit)
        # print(coef)
        dc_coef = dc_coef + coef
        matrix[0][0] = dc_coef

        now_idx = 1
        while now_idx < 64:
            now_word = ""
            while now_word not in self.AC_huff[ac_idx]:
                a = st.GetBit()
                if a == "done":
                    return matrix, dc_coef
                now_word += a
            now_data = bin(self.AC_huff[ac_idx][now_word])[2:]
            now_data = "0"*(8-len(now_data)) + now_data
            print(now_word, now_data)
            if now_data == "00000000":
                return matrix, dc_coef
            if now_data == "11110000":
                now_idx += 16
                continue
            # print(now_idx, int(now_data[:4], 2))
            now_idx += int(now_data[:4], 2)
            m_code = ""
            for _ in range(int(now_data[4:], 2)):
                m_code += st.GetBit()
            print(now_word, now_data, m_code, now_idx)
            matrix = self.fill_matrix(matrix, now_idx, self.magnitude(m_code))
            now_idx += 1
            
        return matrix, dc_coef
        
    def magnitude(self, codeword):
        if codeword[0] == "0":
            new_bit = ""
            for i in range(len(codeword)):
                new_bit += "0" if codeword[i] == "1" else "1"
            coef = -int(new_bit, 2)
        else:
            coef = int(codeword, 2)
        
        return coef
    
    def fill_matrix(self, matrix, idx, data):
        reverse = False
        if idx > 35:
            reverse = True
            idx = 63 - idx
        start = 0
        it = 2
        row = 0
        while start < idx:
            start += it
            it += 1
            row += 1
        fix = start - idx
        i, j = row - fix, fix
        if row % 2 == 0:
            i, j = j, i
        if reverse:
            i, j = 7 - i, 7 - j
        
        matrix[i][j] = data

        return matrix


class Stream:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.total = len(data) * 8

    def GetBit(self):
        try:
            b = self.data[self.pos >> 3]
            s = 7 - (self.pos & 0x7)
            self.pos += 1
            return str((b >> s) & 1)
        except IndexError:
            return "done"
    
    def GetPos(self):
        return self.pos

    def GetRemain(self):
        return self.total - self.pos
    
    def Get10not(self):
        code = ""
        for _ in range(20):
            code += self.GetBit()
        self.pos -= 20
        return code

if __name__ == "__main__":
    file_name = sys.argv[1]
    decoder = JPEG_decoder(f"{file_name}", file_name)
    decoder.decode()
    # print(hex(255) == "0xff")
