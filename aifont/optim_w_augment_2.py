# AUTOGENERATED! DO NOT EDIT! File to edit: 10_optimising_with_aug_run_2.ipynb (unless otherwise specified).

__all__ = ['get_match_font_learner', 'get_learner']

# Cell
from .core import *
from .fontlearner import *
from .fontsampler import *
from .ocrlearner import *
from collections import OrderedDict
from enum import Enum, auto
from fastai.data.all import *
from fastai.vision.all import *
import gc
from nbdev.showdoc import *
from pandas import DataFrame
from PIL.ImageOps import invert
import pydiffvg
import torch
from typing import Callable, List, Protocol, Tuple, Union

# Cell
def get_match_font_learner(seed = 42,
    font_fn = "Arial.ttf",
    font_size = .8,
    samples=3, # We don't care so much about noise here
    **kwargs
    ) -> VectorLearner:
    gc.collect()
    cb = DebugCB(vocal=False)
    learner = create_font_learner(loss_type=LossType.MATCH_FONT,
                                  match_font_path=SYS_FONT_PATH/font_fn,
                                  match_font_size=font_size,
                                  letters=None,
                                  cbs=cb,
                                  folder=None,
                                  n_colors_out=1,
                                  lr=1e-2,
                                  init_range=2.,
                                  seed=seed,
                                  samples=samples,
                                  **kwargs)
    return learner

# Cell
def get_learner(seed = 42,
    version = "aug",
    use_ocr_tfms = True,
    tfms_p = 1.,
    tfms_set = "xstrong2",
    **kwargs
    ) -> VectorLearner:
    gc.collect()
    if 'ocr_model' not in locals() or ocr_model is None:
        ocr_model = load_ocr_model(arch=kaggle_cnn_a_with_res,
                                   df=get_combined_az_and_tmnist_df,
                                   version=version)
    cb = DebugCB(vocal=False)
    ocr_tfms = None
    if use_ocr_tfms:
        # These are the same ones as used for the OCR model
        max_rotate = 15.0
        max_warp = .25
        size = 28
        if   tfms_set == "strong":           blur = GaussianBlur(p=tfms_p, random_size=(5, 9), sigma=10.)
        elif tfms_set.startswith("xstrong"): blur = GaussianBlur(p=tfms_p, kernel_size=(9, 9), sigma=10.)
        else:                                blur = GaussianBlur(p=tfms_p, random_size=5)
        noise = Noise(p=tfms_p, f=(0., .6))
        translate = TranslateAndPad(p=tfms_p)
        tfms = aug_transforms(mult=1.0, do_flip=False, flip_vert=False, max_rotate=max_rotate,
                              min_zoom=0.85, max_zoom=1.15, max_warp=max_warp, p_affine=tfms_p,
                              p_lighting=0., xtra_tfms=None, size=size, mode='bilinear',
                              pad_mode='reflection', align_corners=True, batch=False,
                              min_scale=1.0)
        warp = tfms[0]
        ocr_tfms = [warp, blur]
        if tfms_set == "default":  ocr_tfms += noise
        if tfms_set == "xstrong2": ocr_tfms = [translate, blur]
    learner = create_font_learner(ocr_tfms=ocr_tfms,
                                letters=None,
                                cbs=cb,
                                folder=None,
                                ocr_model=ocr_model,
                                n_colors_out=1,
                                lr=1e-1,
                                init_range=2.,
                                seed=seed,
                                **kwargs)
    if use_ocr_tfms: assert len(learner.loss_func.ocr_loss.tfms) == len(ocr_tfms)
    return learner