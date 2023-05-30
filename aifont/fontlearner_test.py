# AUTOGENERATED! DO NOT EDIT! File to edit: 01_fontlearnertests.ipynb (unless otherwise specified).

__all__ = ['create_vector_learner']

# Cell
from .core import *
from .fontlearner import *
from .ocrlearner import *

import ffmpeg
import gc
import IPython.display
import numpy as np
import PIL
import pydiffvg
import torch
from torch import Tensor
import skimage
import skimage.io
import subprocess
from typing import Callable, List, Protocol, Tuple, Union
from warnings import warn
from fastai.data.all import *
from fastai.vision.all import *

# Cell

def create_vector_learner(bs = 1, epoch_len = 10, cut = 5, img_size = None, ocr_learner = None,
                          folder = "results/test_3c_ATI", normalise = True, vector_class = ATIVectorRL,
                          n_colors_out = 1, init_range = .5,
                          max_distance = 0.6363285714285715, # AZ_STATS['letter_height_mean'] / vector_learner.model[1].canvas_height
                          eps = 1e-6, lr = 1e-2, debug = False, seed = None, cbs = None):

    if ocr_learner is None:
        ocr_learner = get_ocr_model(cut=cut,
                                    img_size=img_size)
    ocr_model = ocr_learner.model
    vocab = get_vocab(ocr_learner)
    raster_norm = ocr_learner.dls.train.after_batch[1] if normalise else None
    ocr_img = ocr_learner.dls.train_ds[0][0]
    canvas_width = ocr_img.width
    canvas_height = ocr_img.height

    dl = LetterDL(vocab=vocab,
                  letters=("A",),
                  epoch_len=epoch_len,
                  bs=bs)
    dls = DataLoaders(dl, dl)

    image_saver = ImageSaver(folder=folder)
    render_layer = vector_class(vocab=vocab,
                                raster_norm=raster_norm,
                                rendered_callback=image_saver,
                                canvas_width=canvas_width,
                                canvas_height=canvas_height,
                                n_colors_out=n_colors_out,
                                max_distance=max_distance,
                                eps=eps)
    n_distance_params = render_layer.n_distance_params
    n_width_params = render_layer.n_width_params
    param_layer = FontParamLayer(n_distance_params=n_distance_params,
                                 n_width_params=n_width_params,
                                 seed=seed,
                                 init_range=init_range)

    font_model = torch.nn.Sequential(param_layer,
                                     render_layer)
                                     #Debugger())

    # Params will be added by Learner
    get_optim = partial(Adam, lr=lr,
                              mom=.5,
                              sqr_mom=.9,
                              wd=0.) # NB. Eps can be also modified

    loss = OCRAndParamLoss(ocr_model=ocr_model,
                           param_layer=param_layer,
                           debug=debug)

    vector_learner = VectorLearner(dls=dls,
                                   model=font_model,
                                   loss_func=loss,
                                   opt_func=get_optim,
                                   cbs=cbs,
                                   image_saver=image_saver)

    return vector_learner, image_saver