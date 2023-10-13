import inspect
import io
import json
from flask import send_file
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import werkzeug

# default int is unsigned - https://github.com/pallets/flask/issues/2643
class SignedIntConverter(werkzeug.routing.IntegerConverter):regex = r'-?\d+'

def get_default_args(func):
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }

def read_csv_file(file_path,sep=' ',names=None):
    try:
        df = pd.read_csv(file_path,sep=' ',names=names)
    except FileNotFoundError as e:
        print(e)
        df = None
    return df

def fig_to_img(fig, dpi=100, transparent=True, close=False):
    """Convert a Matplotlib figure to a PIL Image and return it"""
    buf = io.BytesIO()
    fig.savefig(buf, dpi=dpi, transparent=transparent)
    if close:
        plt.close(fig)
    buf.seek(0)
    img = Image.open(buf)
    return img

def serve_pil_image(pil_img):
    img_io = io.BytesIO()
    pil_img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

def downsample(signal, length):
    return signal
    # use linear interpolation
    # endpoint keyword means than linspace doesn't go all the way to 1.0
    # If it did, there are some off-by-one errors
    # e.g. scale=2.0, [1,2,3] should go to [1,1.5,2,2.5,3,3]
    # but with endpoint=True, we get [1,1.4,1.8,2.2,2.6,3]
    # Both are OK, but since resampling will often involve
    # exact ratios (i.e. for 44100 to 22050 or vice versa)
    # using endpoint=False gets less noise in the resampled sound
    resampled_signal = np.interp(
        np.linspace(0.0, 1.0, length, endpoint=False),  # where to interpret
        np.linspace(0.0, 1.0, signal.shape[0], endpoint=False),  # known positions
        signal,  # known data points
    )
    return resampled_signal