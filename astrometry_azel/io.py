#!/usr/bin/env python
"""
Image stack -> average -> write FITS
Michael Hirsch

Because ImageJ has been a little buggy about writing FITS files, in particular the header
that astrometry.net then crashes on, we wrote this quick script to ingest a variety
of files and average the specified frames then write a FITS.
The reason we average a selected stack of images is to reduce the noise for use in
astrometry.net

The error you might get from an ImageJ saved FITS when reading in:
PyFits, AstroPy, or ImageMagick is:
IOError: Header missing END card.
"""
from pathlib import Path
import numpy as np
from numpy import rot90
from astropy.io import fits
import imageio
from typing import Tuple, Optional
import h5py
from datetime import datetime
from scipy.io import loadmat


def meanstack(infn: Path, Navg: int, ut1: Optional[datetime]=None,
              method: str='mean') -> Tuple[np.ndarray, Optional[datetime]]:
    infn = Path(infn).expanduser()
# %% parse indicies to load
    if isinstance(Navg, slice):
        key = Navg
    elif isinstance(Navg, int):
        key = slice(0, Navg)
    elif len(Navg) == 1:
        key = slice(0, Navg[0])
    elif len(Navg) == 2:
        key = slice(Navg[0], Navg[1])
    else:
        raise ValueError(f'not sure what you mean by Navg={Navg}')
# %% load images
    """
    some methods handled individually to improve efficiency with huge files
    """
    if infn.suffix == '.h5':
        with h5py.File(infn, 'r') as f:
            img = collapsestack(f['/rawimg'], key, method)
# %% time
            if ut1 is None:
                try:
                    ut1 = f['/ut1_unix'][key][0]
                except KeyError:
                    pass
# %% orientation
            try:
                img = rot90(img, k=f['/params']['rotccw'])
            except KeyError:
                pass
    elif infn.suffix == '.fits':
        with fits.open(infn, mode='readonly', memmap=False) as f:  # mmap doesn't work with BZERO/BSCALE/BLANK
            img = collapsestack(f[0].data, key, method)
    elif infn.suffix == '.mat':
        img = loadmat(infn)
        img = collapsestack(img['data'].T, key, method)  # matlab is fortran order
    else:  # .tif etc.
        img = imageio.imread(infn, as_gray=True)
        if img.ndim in (3, 4) and img.shape[-1] == 3:  # assume RGB
            img = collapsestack(img, key, method)

    return img, ut1


def collapsestack(img: np.ndarray, key: slice, method):
    if img.ndim == 2:
        return img
# %%
    if img.ndim == 3:
        if method == 'mean':
            func = np.mean
        elif method == 'median':
            func = np.median
        else:
            raise TypeError(f'unknown method {method}')

        return func(img[key, ...], axis=0).astype(img.dtype)


def writefits(img: np.ndarray, outfn: Path):
    outfn = Path(outfn).expanduser()
    print('writing', outfn)

    f = fits.PrimaryHDU(img)
    f.writeto(outfn, clobber=True, checksum=True)
    # no close
