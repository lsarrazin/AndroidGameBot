
from PIL import Image


def pixbuf2image(self, pix):
    """Convert gdkpixbuf to PIL image"""
    data = pix.get_pixels()
    w = pix.props.width
    h = pix.props.height
    stride = pix.props.rowstride
    mode = "RGBA" if pix.props.has_alpha else "RGB"
    '''
    mode = "RGB"
    if pix.props.has_alpha == True:
        mode = "RGBA"
    '''
    im = Image.frombytes(mode, (w, h), data, "raw", mode, stride)
    return im


