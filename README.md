# pyTGA
A simple Python module to manage **TGA** *images* This module is compatible with **Python 2** and **Python 3**.

The library supports at the moment these kind of formats:

* Uncompressed Grayscale - 8 bit depth
* Uncompressed RGB - 24 bit depth
* Uncompressed RGBA - 32 bit depth

As you can see in the example you can use the python basic types for data.

## Install

Simply type:
```bash
python setup.py install
```

## Test

```bash
cd test
python test_module.py
```

## Example

```python
import pyTGA


def main():
    data_bw = [
        [0, 255, 0, 0],
        [0, 0, 255, 0],
        [255, 255, 255, 0]
    ]

    data_rgb = [
        [(0, 0, 0), (255, 0, 0), (0, 0, 0), (0, 0, 0)],
        [(0, 0, 0), (0, 0, 0), (255, 0, 0), (0, 0, 0)],
        [(255, 0, 0), (255, 0, 0), (255, 0, 0), (0, 0, 0)]
    ]

    data_rgba = [
        [(0, 0, 0, 0), (255, 0, 0, 150), (0, 0, 0, 0), (0, 0, 0, 0)],
        [(0, 0, 0, 0), (0, 0, 0, 0), (255, 0, 0, 150), (0, 0, 0, 0)],
        [(255, 0, 0, 150), (255, 0, 0, 150), (255, 0, 0, 150), (0, 0, 0, 0)]
    ]

    ##
    # Create from grayscale data
    image = pyTGA.Image(data=data_bw)
    # Save as TGA
    image.save("image_black_and_white")

    ##
    # Create from RGB data
    image = pyTGA.Image(data=data_rgb)
    image.save("image_rgb")

    ##
    # Create from RGBA data
    image = pyTGA.Image(data=data_rgba)
    image.save("image_rgba")

    ##
    # Load and modify an image
    image = pyTGA.Image()
    image.load("image_black_and_white.tga").set_pixel(0, 3, 175)
    image.save("image_black_and_white_mod.tga")

    # Get some data
    print(image.get_pixel(0, 3))
    print(image.get_pixels())

if __name__ == '__main__':
    main()
```
