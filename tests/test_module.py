import unittest
import os


class TestStringMethods(unittest.TestCase):

    def test_black_and_white_image(self):
        import pyTGA

        data_bw = [
            [0, 255, 0, 0],
            [0, 0, 255, 0],
            [255, 255, 255, 0]
        ]

        image = pyTGA.Image(data=data_bw)
        image.save("test_bw")

        image2 = pyTGA.Image()
        image2.load("test_bw.tga")

        self.assertEqual(image.get_pixels(), image2.get_pixels())

        os.remove("test_bw.tga")

    def test_RGB_image(self):
        import pyTGA

        data_rgb = [
            [(0, 0, 0), (255, 0, 0), (0, 0, 0), (0, 0, 0)],
            [(0, 0, 0), (0, 0, 0), (255, 0, 0), (0, 0, 0)],
            [(255, 0, 0), (255, 0, 0), (255, 0, 0), (0, 0, 0)]
        ]

        image = pyTGA.Image(data=data_rgb)
        image.save("test_rgb")

        image2 = pyTGA.Image()
        image2.load("test_rgb.tga")

        self.assertEqual(image.get_pixels(), image2.get_pixels())

        os.remove("test_rgb.tga")

    def test_RGBA_image(self):
        import pyTGA

        data_rgba = [
            [(0, 0, 0, 0), (255, 0, 0, 150), (0, 0, 0, 0), (0, 0, 0, 0)],
            [(0, 0, 0, 0), (0, 0, 0, 0), (255, 0, 0, 150), (0, 0, 0, 0)],
            [(255, 0, 0, 150), (255, 0, 0, 150),
             (255, 0, 0, 150), (0, 0, 0, 0)]
        ]

        image = pyTGA.Image(data=data_rgba)
        image.save("test_rgba")

        image2 = pyTGA.Image()
        image2.load("test_rgba.tga")

        self.assertEqual(image.get_pixels(), image2.get_pixels())

        os.remove("test_rgba.tga")

    def test_modify_pixel(self):
        import pyTGA

        data_rgba = [
            [(0, 0, 0, 0), (255, 0, 0, 150), (0, 0, 0, 0), (0, 0, 0, 0)],
            [(0, 0, 0, 0), (0, 0, 0, 0), (255, 0, 0, 150), (0, 0, 0, 0)],
            [(255, 0, 0, 150), (255, 0, 0, 150),
             (255, 0, 0, 150), (0, 0, 0, 0)]
        ]

        image = pyTGA.Image(data=data_rgba)
        image.save("test_mod_rgba")

        image2 = pyTGA.Image(data=data_rgba)
        image2.set_pixel(0, 3, (0, 255, 0, 55))
        image2.save("test_mod_rgba_2")

        image2 = pyTGA.Image()
        image2.load("test_mod_rgba_2.tga")

        self.assertNotEqual(image.get_pixels(), image2.get_pixels())
        self.assertEqual(image.get_pixel(0, 3), (0, 0, 0, 0))
        self.assertEqual(image2.get_pixel(0, 3), (0, 255, 0, 55))

        os.remove("test_mod_rgba.tga")
        os.remove("test_mod_rgba_2.tga")

    def test_original_format(self):
        import pyTGA

        data_rgba = [
            [(0, 0, 0, 0), (255, 0, 0, 150), (0, 0, 0, 0), (0, 0, 0, 0)],
            [(0, 0, 0, 0), (0, 0, 0, 0), (255, 0, 0, 150), (0, 0, 0, 0)],
            [(255, 0, 0, 150), (255, 0, 0, 150),
             (255, 0, 0, 150), (0, 0, 0, 0)]
        ]

        image = pyTGA.Image(data=data_rgba)
        image.save("test_original_rgba", original_format=True)

        image2 = pyTGA.Image()
        image2.load("test_original_rgba.tga")

        self.assertTrue(image2.is_original_format())

        os.remove("test_original_rgba.tga")

    def test_new_format(self):
        import pyTGA

        data_rgba = [
            [(0, 0, 0, 0), (255, 0, 0, 150), (0, 0, 0, 0), (0, 0, 0, 0)],
            [(0, 0, 0, 0), (0, 0, 0, 0), (255, 0, 0, 150), (0, 0, 0, 0)],
            [(255, 0, 0, 150), (255, 0, 0, 150),
             (255, 0, 0, 150), (0, 0, 0, 0)]
        ]

        image = pyTGA.Image(data=data_rgba)
        image.save("test_new_format_rgba")

        image2 = pyTGA.Image()
        image2.load("test_new_format_rgba.tga")

        self.assertFalse(image2.is_original_format())

        os.remove("test_new_format_rgba.tga")

    def test_test_16_bits(self):
        import pyTGA

        data_rgb = [
            [(0, 0, 0), (255, 0, 0), (0, 0, 0), (0, 0, 0)],
            [(0, 0, 0), (0, 0, 0), (255, 0, 0), (0, 0, 0)],
            [(255, 0, 0), (255, 0, 0), (255, 0, 0), (0, 0, 0)]
        ]

        data_rgb_16 = [
            [(0, 0, 0), (31, 0, 0), (0, 0, 0), (0, 0, 0)],
            [(0, 0, 0), (0, 0, 0), (31, 0, 0), (0, 0, 0)],
            [(31, 0, 0), (31, 0, 0), (31, 0, 0), (0, 0, 0)]
        ]

        image = pyTGA.Image(data=data_rgb)
        image.save("test_16", force_16_bit=True)

        image2 = pyTGA.Image()
        image2.load("test_16.tga")

        self.assertEqual(image2.get_pixels(), data_rgb_16)

        os.remove("test_16.tga")

if __name__ == '__main__':
    unittest.main()
