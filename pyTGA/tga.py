from __future__ import unicode_literals, print_function
from sys import version_info
from copy import deepcopy

__all__ = ["Image", "ImageError", "VERSION"]


VERSION = "1.0.0"


def dec_byte(data, size=1, endian='little'):
    if endian == 'little':
        data = bytes(bytearray(reversed(data)))

    res = 0b0
    for step in range(size):
        if version_info[0] < 3:
            res = res << 8*step | int(data[step].encode("hex"), 16)
        else:
            res = res << 8*step | data[step]

    return res


def multiple_dec_byte(stream, num, size=1, endian='little'):
    return [dec_byte(stream.read(size), size, endian) for number in range(num)]


def gen_byte(data, size=1, endian='little'):
    _list = []
    mask = 255  # 11111111

    for step in reversed(range(size)):
        _list.append((data & (mask << 8*step)) >> 8*step)

    if endian == 'little':
        _list = list(reversed(_list))

    return bytes(bytearray(_list))


def gen_pixel_rgba(c_r, c_g, c_b, alpha=None):
    tmp = bytearray()

    # little endian: RGB -> BGR
    tmp += gen_byte(c_b)
    tmp += gen_byte(c_g)
    tmp += gen_byte(c_r)
    if alpha is not None:
        tmp += gen_byte(alpha)

    return tmp


def gen_pixel_rgb_16(c_r, c_g, c_b):
    tmp = bytearray()

    first_byte = 0b0
    first_byte |= (c_r & 0b11111) << 3
    first_byte |= (c_g & 0b11100) >> 2

    second_byte = 0b0
    second_byte |= (c_g & 0b00011) << 6
    second_byte |= (c_b & 0b11111) << 1
    ##
    # alpha is not useful but
    # is inserted like the standard whant
    # - 1 : is visible
    # - 0 : is not visible
    #
    second_byte |= 0b1

    # little endian: RGB -> BGR
    tmp += gen_byte(second_byte)
    tmp += gen_byte(first_byte)

    return tmp


def get_rgb_from_16(second_byte, first_byte):
    # Args are inverted because is little endian
    c_r = (first_byte & 0b11111000) >> 3
    c_g = (first_byte & 0b00000111) << 5
    c_g |= (second_byte & 0b11000000) >> 6
    c_b = (second_byte & 0b00111110) >> 1

    return (c_r, c_g, c_b)


class TGAHeader(object):

    def __init__(self):
        ##
        # ID LENGTH (1 byte):
        #   Number of bites of field 6, max 255.
        #   Is 0 if no image id is present.
        #
        self.id_length = 0
        ##
        # COLOR MAP TYPE (1 byte):
        #   - 0 : no color map included with the image
        #   - 1 : color map included with the image
        #
        self.color_map_type = 0
        ##
        # IMAGE TYPE (1 byte):
        #   - 0  : no data included
        #   - 1  : uncompressed color map image
        #   - 2  : uncompressed true color image
        #   - 3  : uncompressed black and white image
        #   - 9  : run-length encoded color map image
        #   - 10 : run-length encoded true color image
        #   - 11 : run-length encoded black and white image
        #
        self.image_type = 0
        ##
        # COLOR MAP SPECIFICATION (5 bytes):
        #   - first_entry_index (2 bytes) : index of first color map entry
        #   - color_map_length  (2 bytes)
        #   - color_map_entry_size (1 byte)
        #
        self.first_entry_index = 0
        self.color_map_length = 0
        self.color_map_entry_size = 0
        ##
        # IMAGE SPECIFICATION (10 bytes):
        #   - x_origin  (2 bytes)
        #   - y_origin  (2 bytes)
        #   - image_width   (2 bytes)
        #   - image_height  (2 bytes)
        #   - pixel_depht   (1 byte):
        #       - 8 bit  : grayscale
        #       - 16 bit : RGB (5-5-5-1) bit per color
        #                  Last one is alpha (visible or not)
        #       - 24 bit : RGB (8-8-8) bit per color
        #       - 32 bit : RGBA (8-8-8-8) bit per color
        #   - image_descriptor (1 byte):
        #       - bit 3-0 : number of attribute bit per pixel
        #       - bit 5-4 : order in which pixel data is transferred
        #                   from the file to the screen
        #  +-----------------------------------+-------------+-------------+
        #  | Screen destination of first pixel | Image bit 5 | Image bit 4 |
        #  +-----------------------------------+-------------+-------------+
        #  | bottom left                       |           0 |           0 |
        #  | bottom right                      |           0 |           1 |
        #  | top left                          |           1 |           0 |
        #  | top right                         |           1 |           1 |
        #  +-----------------------------------+-------------+-------------+
        #       - bit 7-6 : must be zero to insure future compatibility
        #
        self.x_origin = 0
        self.y_origin = 0
        self.image_width = 0
        self.image_height = 0
        self.pixel_depht = 0
        self.image_descriptor = 0

    def to_bytes(self):
        tmp = bytearray()

        tmp += gen_byte(self.id_length)
        tmp += gen_byte(self.color_map_type)
        tmp += gen_byte(self.image_type)
        tmp += gen_byte(self.first_entry_index, 2)
        tmp += gen_byte(self.color_map_length, 2)
        tmp += gen_byte(self.color_map_entry_size)
        tmp += gen_byte(self.x_origin, 2)
        tmp += gen_byte(self.y_origin, 2)
        tmp += gen_byte(self.image_width, 2)
        tmp += gen_byte(self.image_height, 2)
        tmp += gen_byte(self.pixel_depht)
        tmp += gen_byte(self.image_descriptor)

        return tmp


class TGAFooter(object):

    def __init__(self):
        self.extension_area_offset = 0  # 4 bytes
        self.developer_directory_offset = 0  # 4 bytes
        self.__signature = bytes(
            bytearray("TRUEVISION-XFILE".encode('ascii')))  # 16 bytes
        self.__dot = bytes(bytearray('.'.encode('ascii')))  # 1 byte
        self.__end = bytes(bytearray([0]))  # 1 byte

    def to_bytes(self):
        tmp = bytearray()

        tmp += gen_byte(self.extension_area_offset, 4)
        tmp += gen_byte(self.developer_directory_offset, 4)
        tmp += self.__signature
        tmp += self.__dot
        tmp += self.__end

        return tmp


class ImageError(Exception):

    def __init__(self, msg, errname):
        super(ImageError, self).__init__(msg)
        error_map = {
            'pixel_dest_position': -10,
            'bad_row_length': -21,
            'bad_pixel_length': -22,
            'bad_pixel_value': -23,
            'non_supported_type': -31,
        }
        self.errno = error_map.get(errname, None)


class Image(object):

    def __init__(self, data=None):
        self._pixels = None

        if data is not None:
            self.check(data)
            self._pixels = deepcopy(data)

        # Screen destination of first pixel
        self.__bottom_left = 0b0
        self.__bottom_right = 0b1 << 4
        self.__top_left = 0b1 << 5
        self.__top_right = 0b1 << 4 | 0b1 << 5

        # Default values
        self._first_pixel = self.__top_left
        self._header = TGAHeader()
        self._footer = TGAFooter()
        self.__new_TGA_format = True

    @staticmethod
    def check(data):
        tmp_len = len(data[0])
        row_num = 0
        for row in data:
            row_num += 1
            if len(row) != tmp_len:
                raise ImageError(
                    "row number {0} has different length from first row".format(
                        row_num),
                    'bad_row_length'
                )
            for pixel in row:
                if type(pixel) == tuple:
                    if len(pixel) < 3 or len(pixel) > 4:
                        raise ImageError(
                            "'{0}' is not a valid pixel tuple".format(pixel),
                            'bad_pixel_length'
                        )
                elif type(pixel) != int:
                    raise ImageError(
                        "'{0}' is not a valid pixel value".format(pixel),
                        'bad_pixel_value'
                    )

    def set_first_pixel_destination(self, dest):
        if dest.lower() == 'bl':
            self._first_pixel = self.__bottom_left
            return self
        elif dest.lower() == 'br':
            self._first_pixel = self.__bottom_right
            return self
        elif dest.lower() == 'tl':
            self._first_pixel = self.__top_left
            return self
        elif dest.lower() == 'tr':
            self._first_pixel = self.__top_right
            return self
        else:
            raise ImageError(
                "'{0}' is not a valid pixel destination".format(dest),
                'pixel_dest_position'
            )

    def is_original_format(self):
        return not self.__new_TGA_format

    def set_pixel(self, row, col, value):
        self._pixels[row][col] = value
        return self

    def get_pixel(self, row, col):
        return self._pixels[row][col]

    def get_pixels(self):
        return self._pixels

    def load(self, file_name):
        with open(file_name, "rb") as image_file:
            # Check footer
            image_file.seek(-26, 2)
            self._footer.extension_area_offset = dec_byte(
                image_file.read(4), 4)
            self._footer.developer_directory_offset = dec_byte(
                image_file.read(4), 4)
            signature = image_file.read(16)
            dot = image_file.read(1)
            zero = dec_byte(image_file.read(1))

            if signature == "TRUEVISION-XFILE".encode('ascii') and\
                    dot == ".".encode('ascii') and zero == 0:
                self.__new_TGA_format = True
            else:
                self.__new_TGA_format = False

            # Read Header
            image_file.seek(0)
            # ID LENGTH
            self._header.id_length = dec_byte(image_file.read(1))
            # COLOR MAP TYPE
            self._header.color_map_type = dec_byte(image_file.read(1))
            # IMAGE TYPE
            self._header.image_type = dec_byte(image_file.read(1))
            # COLOR MAP SPECIFICATION
            self._header.first_entry_index = dec_byte(image_file.read(2), 2)
            self._header.color_map_length = dec_byte(image_file.read(2), 2)
            self._header.color_map_entry_size = dec_byte(image_file.read(1))
            # IMAGE SPECIFICATION
            self._header.x_origin = dec_byte(image_file.read(2), 2)
            self._header.y_origin = dec_byte(image_file.read(2), 2)
            self._header.image_width = dec_byte(image_file.read(2), 2)
            self._header.image_height = dec_byte(image_file.read(2), 2)
            self._header.pixel_depht = dec_byte(image_file.read(1))
            self._header.image_descriptor = dec_byte(image_file.read(1))

            self._pixels = []
            if self._header.image_type == 2 or\
                    self._header.image_type == 3:
                for row in range(self._header.image_height):
                    self._pixels.append([])
                    for col in range(self._header.image_width):
                        if self._header.image_type == 3:
                            self._pixels[row].append(
                                dec_byte(image_file.read(1)))
                        elif self._header.image_type == 2:
                            if self._header.pixel_depht == 16:
                                first_b, second_b = multiple_dec_byte(
                                    image_file, 2)
                                self._pixels[row].append(
                                    get_rgb_from_16(first_b, second_b))
                            elif self._header.pixel_depht == 24:
                                c_b, c_g, c_r = multiple_dec_byte(
                                    image_file, 3)
                                self._pixels[row].append((c_r, c_g, c_b))
                            elif self._header.pixel_depht == 32:
                                c_b, c_g, c_r, alpha = multiple_dec_byte(
                                    image_file, 4)
                                self._pixels[row].append(
                                    (c_r, c_g, c_b, alpha))
                        else:
                            raise ImageError(
                                "type num '{0}'' is not supported".format(
                                    self._header.image_type),
                                'non_supported_type'
                            )
            ##
            # Decode
            #
            elif self._header.image_type == 10 or\
                    self._header.image_type == 11:
                self._pixels.append([])
                while len(self._pixels) != self._header.image_height or\
                        len(self._pixels[-1]) != self._header.image_width:
                    if len(self._pixels[-1]) == self._header.image_width:
                        self._pixels.append([])
                    repetition_count = dec_byte(image_file.read(1))
                    RLE = (repetition_count & 0b10000000) >> 7 == 1
                    count = (repetition_count & 0b01111111) + 1
                    if RLE:
                        pixel = None
                        if self._header.image_type == 11:
                            pixel = dec_byte(image_file.read(1))
                        elif self._header.image_type == 10:
                            if self._header.pixel_depht == 16:
                                first_b, second_b = multiple_dec_byte(
                                    image_file, 2)
                                pixel = get_rgb_from_16(first_b, second_b)
                            elif self._header.pixel_depht == 24:
                                c_b, c_g, c_r = multiple_dec_byte(
                                    image_file, 3)
                                pixel = (c_r, c_g, c_b)
                            elif self._header.pixel_depht == 32:
                                c_b, c_g, c_r, alpha = multiple_dec_byte(
                                    image_file, 4)
                                pixel = (c_r, c_g, c_b, alpha)
                        else:
                            raise ImageError(
                                "type num '{0}'' is not supported".format(
                                    self._header.image_type),
                                'non_supported_type'
                            )
                        for num in range(count):
                            self._pixels[-1].append(pixel)
                    else:
                        for num in range(count):
                            if self._header.image_type == 11:
                                self._pixels[-1].append(
                                    dec_byte(image_file.read(1)))
                            elif self._header.image_type == 10:
                                if self._header.pixel_depht == 16:
                                    first_b, second_b = multiple_dec_byte(
                                        image_file, 2, 1)
                                    self._pixels[-1].append(
                                        get_rgb_from_16(first_b, second_b))
                                elif self._header.pixel_depht == 24:
                                    c_b, c_g, c_r = multiple_dec_byte(
                                        image_file, 3, 1)
                                    self._pixels[-1].append((c_r, c_g, c_b))
                                elif self._header.pixel_depht == 32:
                                    c_b, c_g, c_r, alpha = multiple_dec_byte(
                                        image_file, 4, 1)
                                    self._pixels[-1].append(
                                        (c_r, c_g, c_b, alpha))
                            else:
                                raise ImageError(
                                    "type num '{0}'' is not supported".format(
                                        self._header.image_type),
                                    'non_supported_type'
                                )
        return self

    def save(self, file_name, original_format=False, force_16_bit=False,
             compress=False):
        # ID LENGTH
        self._header.id_length = 0
        # COLOR MAP TYPE
        self._header.color_map_type = 0
        # COLOR MAP SPECIFICATION
        self._header.first_entry_index = 0
        self._header.color_map_length = 0
        self._header.color_map_entry_size = 0
        # IMAGE SPECIFICATION
        self._header.x_origin = 0
        self._header.y_origin = 0
        self._header.image_width = len(self._pixels[0])
        self._header.image_height = len(self._pixels)
        self._header.image_descriptor = 0b0 | self._first_pixel

        ##
        # IMAGE TYPE
        # IMAGE SPECIFICATION (pixel_depht)
        tmp_pixel = self._pixels[0][0]
        if type(tmp_pixel) == int:
            self._header.image_type = 3
            self._header.pixel_depht = 8
        elif type(tmp_pixel) == tuple:
            self._header.image_type = 2
            if len(tmp_pixel) == 3:
                if not force_16_bit:
                    self._header.pixel_depht = 24
                else:
                    self._header.pixel_depht = 16
            elif len(tmp_pixel) == 4:
                self._header.pixel_depht = 32

        if compress:
            if self._header.image_type == 3:
                self._header.image_type = 11
            elif self._header.image_type == 2:
                self._header.image_type = 10

        with open("{0:s}.tga".format(file_name), "wb") as image_file:
            image_file.write(self._header.to_bytes())

            if not compress:
                for row in self._pixels:
                    for pixel in row:
                        if self._header.image_type == 3:
                            image_file.write(gen_byte(pixel))
                        elif self._header.image_type == 2:
                            if self._header.pixel_depht == 16:
                                image_file.write(gen_pixel_rgb_16(*pixel))
                            elif self._header.pixel_depht == 24:
                                image_file.write(gen_pixel_rgba(*pixel))
                            elif self._header.pixel_depht == 32:
                                image_file.write(gen_pixel_rgba(*pixel))
            else:
                for row in self._pixels:
                    for repetition_count, pixel_value in self._encode(row):
                        image_file.write(gen_byte(repetition_count))
                        if repetition_count > 127:
                            if self._header.image_type == 11:
                                image_file.write(gen_byte(pixel_value))
                            elif self._header.image_type == 10:
                                if self._header.pixel_depht == 16:
                                    image_file.write(
                                        gen_pixel_rgb_16(*pixel_value))
                                elif self._header.pixel_depht == 24:
                                    image_file.write(
                                        gen_pixel_rgba(*pixel_value))
                                elif self._header.pixel_depht == 32:
                                    image_file.write(
                                        gen_pixel_rgba(*pixel_value))
                        else:
                            for pixel in pixel_value:
                                if self._header.image_type == 11:
                                    image_file.write(gen_byte(pixel))
                                elif self._header.image_type == 10:
                                    if self._header.pixel_depht == 16:
                                        image_file.write(
                                            gen_pixel_rgb_16(*pixel))
                                    elif self._header.pixel_depht == 24:
                                        image_file.write(
                                            gen_pixel_rgba(*pixel))
                                    elif self._header.pixel_depht == 32:
                                        image_file.write(
                                            gen_pixel_rgba(*pixel))

            if self.__new_TGA_format and not original_format:
                image_file.write(self._footer.to_bytes())

        return self

    @staticmethod
    def _encode(row):
        ##
        # Run-length encoded (RLE) images comprise two types of data
        # elements:Run-length Packets and Raw Packets.
        #
        # The first field (1 byte) of each packet is called the
        # Repetition Count field. The second field is called the
        # Pixel Value field. For Run-length Packets, the Pixel Value
        # field contains a single pixel value. For Raw
        # Packets, the field is a variable number of pixel values.
        #
        # The highest order bit of the Repetition Count indicates
        # whether the packet is a Raw Packet or a Run-length
        # Packet. If bit 7 of the Repetition Count is set to 1, then
        # the packet is a Run-length Packet. If bit 7 is set to
        # zero, then the packet is a Raw Packet.
        #
        # The lower 7 bits of the Repetition Count specify how many
        # pixel values are represented by the packet. In
        # the case of a Run-length packet, this count indicates how
        # many successive pixels have the pixel value
        # specified by the Pixel Value field. For Raw Packets, the
        # Repetition Count specifies how many pixel values
        # are actually contained in the next field. This 7 bit value
        # is actually encoded as 1 less than the number of
        # pixels in the packet (a value of 0 implies 1 pixel while a
        # value of 0x7F implies 128 pixels).
        #
        # Run-length Packets should never encode pixels from more than
        # one scan line. Even if the end of one scan
        # line and the beginning of the next contain pixels of the same
        # value, the two should be encoded as separate
        # packets. In other words, Run-length Packets should not wrap
        # from one line to another. This scheme allows
        # software to create and use a scan line table for rapid, random
        # access of individual lines. Scan line tables are
        # discussed in further detail in the Extension Area section of
        # this document.
        #
        #
        # Pixel format data example:
        #
        # +=======================================+
        # | Uncompressed pixel run                |
        # +=========+=========+=========+=========+
        # | Pixel 0 | Pixel 1 | Pixel 2 | Pixel 3 |
        # +---------+---------+---------+---------+
        # | 144     | 144     | 144     | 144     |
        # +---------+---------+---------+---------+
        #
        # +==========================================+
        # | Run-length Packet                        |
        # +============================+=============+
        # | Repetition Count           | Pixel Value |
        # +----------------------------+-------------+
        # | 1 bit |       7 bit        |             |
        # +----------------------------|     144     |
        # |   1   |  3 (num pixel - 1) |             |
        # +----------------------------+-------------+
        #
        # +====================================================================================+
        # | Raw Packet                                                                         |
        # +============================+=============+=============+=============+=============+
        # | Repetition Count           | Pixel Value | Pixel Value | Pixel Value | Pixel Value |
        # +----------------------------+-------------+-------------+-------------+-------------+
        # | 1 bit |       7 bit        |             |             |             |             |
        # +----------------------------|     144     |     144     |     144     |     144     |
        # |   0   |  3 (num pixel - 1) |             |             |             |             |
        # +----------------------------+-------------+-------------+-------------+-------------+
        #
        repetition_count = None
        pixel_value = None
        ##
        # States:
        # - 0: init
        # - 1: run-length packet
        # - 2: raw packet
        #
        state = 0
        index = 0

        while index != len(row):
            if state == 0:
                repetition_count = 0
                if index == len(row) - 1:
                    pixel_value = [row[index]]
                    yield (repetition_count, pixel_value)
                elif row[index] == row[index + 1]:
                    repetition_count |= 0b10000000
                    pixel_value = row[index]
                    state = 1
                else:
                    pixel_value = [row[index]]
                    state = 2
                index += 1
            elif state == 1 and row[index] == pixel_value:
                if repetition_count & 0b1111111 == 127:
                    yield (repetition_count, pixel_value)
                    repetition_count = 0b10000000
                else:
                    repetition_count += 1
                index += 1
            elif state == 2 and row[index] != pixel_value:
                if repetition_count & 0b1111111 == 127:
                    yield (repetition_count, pixel_value)
                    repetition_count = 0
                    pixel_value = [row[index]]
                else:
                    repetition_count += 1
                    pixel_value.append(row[index])
                index += 1
            else:
                yield (repetition_count, pixel_value)
                state = 0

        if state != 0:
            yield (repetition_count, pixel_value)
