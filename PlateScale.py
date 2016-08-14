#!/usr/bin/env python
"""
script to plate scale data in FITS or HDF5 format.

Michael Hirsch
"""
from astrometry_azel import Path
import h5py
from warnings import warn
#
from astrometry_azel.imgAvgStack import meanstack,writefits
from astrometry_azel.fits2azel import fits2azel

def doplatescale(infn,outfn,latlon,ut1,Navg):
    infn = Path(infn).expanduser()

    if outfn:
        outfn = Path(outfn).expanduser()
    else:
        outfn = infn.with_suffix('.h5')

    fitsfn = outfn.with_suffix('.fits')
#%% convert to mean
    meanimg,ut1 = meanstack(infn,Navg,ut1)
    writefits(meanimg,fitsfn)
#%% try to get site coordinates from file
    if not latlon:
        if infn.suffix=='.h5':
            with h5py.File(str(infn),'r',libver='latest') as f:
                try:
                    latlon = [f['/sensorloc']['glat'], f['/sensorloc']['glon']]
                except KeyError:
                    try:
                        latlon = f['/lla'][:2]
                    except KeyError as e:
                        warn('could not get camera coordinates from {}, will compute only RA/DEC  {}'.format(infn,e))
        else:
            warn('could not get camera coordinates from {}, will compute only RA/DEC'.format(infn))
#%%
    x,y,ra,dec,az,el,timeFrame = fits2azel(fitsfn,latlon,ut1,['show','h5','png'],(0,2800))

if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser(description='do plate scaling for image data')
    p.add_argument('infn',help='image data file name (HDF5 or FITS)')
    p.add_argument('-o','--outfn',help='platescale data path to write')
    p.add_argument('-c','--latlon',help='wgs84 coordinates of cameras (deg.)',nargs=2,type=float)
    p.add_argument('-t','--ut1',help='override file UT1 time yyyy-mm-ddTHH:MM:SSZ')
    p.add_argument('-N','--navg',help='number of frames or start,stop frames to avg',nargs='+',type=int,default=10)
    p = p.parse_args()

    doplatescale(p.infn,p.outfn,p.latlon,p.ut1,p.navg)
