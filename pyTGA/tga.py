from __future__ import unicode_literals, print_function
from sys import version_info
from copy import deepcopy

__all__ = ["Image"]


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
            'pixel_dest_position': -10
        }
        self.errno = error_map.get(errname, None)


class Image(object):

    def __init__(self, data=None):
        self._pixels = deepcopy(data) if data is not None else None

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

    def set_first_pixel_destination(self, dest):
        if dest.lower() == 'bl':
            self._first_pixel = self.__bottom_left
        elif dest.lower() == 'br':
            self._first_pixel = self.__bottom_right
        elif dest.lower() == 'tl':
            self._first_pixel = self.__top_left
        elif dest.lower() == 'tr':
            self._first_pixel = self.__top_right
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
            for row in range(self._header.image_height):
                self._pixels.append([])
                for col in range(self._header.image_width):
                    if self._header.image_type == 3:
                        self._pixels[row].append(
                            dec_byte(image_file.read(1)))
                    elif self._header.image_type == 2:
                        if self._header.pixel_depht == 16:
                            self._pixels[row].append(get_rgb_from_16(dec_byte(
                                image_file.read(1)), dec_byte(
                                image_file.read(1))))
                        elif self._header.pixel_depht == 24:
                            c_b, c_g, c_r=dec_byte(
                                image_file.read(1)), dec_byte(
                                image_file.read(1)), dec_byte(
                                image_file.read(1))
                            self._pixels[row].append((c_r, c_g, c_b))
                        elif self._header.pixel_depht == 32:
                            c_b, c_g, c_r, alpha=dec_byte(
                                image_file.read(1)), dec_byte(
                                image_file.read(1)), dec_byte(
                                image_file.read(1)), dec_byte(
                                image_file.read(1))
                            self._pixels[row].append((c_r, c_g, c_b, alpha))

        return self

    def save(self, file_name, **kwargs):

        original_format=kwargs.get('original_format', False)
        force_16_bit=kwargs.get('force_16_bit', False)

        # ID LENGTH
        self._header.id_length=0
        # COLOR MAP TYPE
        self._header.color_map_type=0
        # COLOR MAP SPECIFICATION
        self._header.first_entry_index=0
        self._header.color_map_length=0
        self._header.color_map_entry_size=0
        # IMAGE SPECIFICATION
        self._header.x_origin=0
        self._header.y_origin=0
        self._header.image_width=len(self._pixels[0])
        self._header.image_height=len(self._pixels)
        self._header.image_descriptor=0b0 | self._first_pixel

        ##
        # IMAGE TYPE
        # IMAGE SPECIFICATION (pixel_depht)
        tmp_pixel=self._pixels[0][0]
        if type(tmp_pixel) == int:
            self._header.image_type=3
            self._header.pixel_depht=8
        elif type(tmp_pixel) == tuple:
            self._header.image_type=2
            if len(tmp_pixel) == 3:
                if not force_16_bit:
                    self._header.pixel_depht=24
                else:
                    self._header.pixel_depht=16
            elif len(tmp_pixel) == 4:
                self._header.pixel_depht=32


        with open("{0:s}.tga".format(file_name), "wb") as image_file:
            image_file.write(self._header.to_bytes())

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


            if self.__new_TGA_format and not original_format:
                image_file.write(self._footer.to_bytes())

        return self
