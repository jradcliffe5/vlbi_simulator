import numpy as np
import os, ast, sys
import casatools
from casatasks import *
from simulator_functions import *
try:
	from astropy.io import fits
except:
	import pyfits as fits
casalog.showconsole(True)

try:
	i = sys.argv.index("-c") + 2
except:
	i = 1
	pass

inputs = headless(sys.argv[i])

## get images
pbs = []
ims = []
cims = []
for i in os.listdir('%s'%inputs['output_path']):
	if i.endswith('.ms.pb'):
		pbs.append("%s/%s"%(inputs['output_path'],i))
	elif i.endswith('.ms_pb.image'):
		ims.append("%s/%s"%(inputs['output_path'],i))
	elif i.endswith('.ms.image'):
		cims.append("%s/%s"%(inputs['output_path'],i))
ims.sort()
pbs.sort()
cims.sort()

lm = casatools.linearmosaic()
rmdirs(['%s/%s_mosaic.linmos'%(inputs['output_path'],inputs['prefix']), '%s/%s_mosaic.weightlinmos'%(inputs['output_path'],inputs['prefix'])])
print('Defining output image')
imsize = np.array(ast.literal_eval(inputs['mosaic_area']))*1.2*3.6e3
max_mosaic_size = 7200
cell = '%.5farcsec'%(imsize/max_mosaic_size)[0]
print(cell)
pc = ast.literal_eval(inputs['field_centre'])
lm.defineoutputimage(nx=max_mosaic_size, cellx=cell,ny=max_mosaic_size, celly=cell, imagecenter='%s %s'%(pc[0],pc[1]), outputimage='%s/%s_mosaic.linmos'%(inputs['output_path'],inputs['prefix']), outputweight='%s/%s_mosaic.weightlinmos'%(inputs['output_path'],inputs['prefix']))
print('Making linear mosaic')

if inputs['clean_rms'] == 'True':
	for i in range(len(cims)):
		lm.makemosaic(images=cims[i], weightimages=pbs[i],weighttype=1,imageweighttype=0)
		exportfits(imagename='%s/%s_mosaic.linmos'%(inputs['output_path'],inputs['prefix']),
		           fitsimage='%s/%s_mosaic.linmos.fits'%(inputs['output_path'],inputs['prefix']),
				   overwrite=True)
		rms = imstat(imagename=cims[i])['rms'].squeeze()
		os.system('rm -r %s.smooth'%cims[i])
		immath(imagename=pbs[i],outfile=cims[i]+'.smooth',expr='%.9f/IM0'%rms)
		os.system('rm -r %s.rg'%cims[i])
		imregrid(imagename=cims[i]+'.smooth',template='%s/%s_mosaic.linmos'%(inputs['output_path'],inputs['prefix']),output=cims[i]+'.rg',overwrite=True)
		os.system('rm -r %s.rg.fits'%cims[i])
		exportfits(imagename=cims[i]+'.rg',fitsimage=cims[i]+'.rg.fits',overwrite=True)
		if i == 0:
			header = fits.open(cims[i]+'.rg.fits')[0].header
			temp_array = fits.open(cims[i]+'.rg.fits')[0].data.squeeze()
		else:    
			temp_array = np.dstack([temp_array,fits.open(cims[i]+'.rg.fits')[0].data.squeeze()])
	output_data = 1/np.sqrt(np.nansum((1/(temp_array*temp_array)),axis=2))
	hdu = fits.open('%s/%s_mosaic.linmos.fits'%(inputs['output_path'],inputs['prefix']))
	hdu[0].data[0,0,:,:] = output_data
	rmfiles(['%s/%s_mosaic.linmos.fits'%(inputs['output_path'],inputs['prefix'])])
	hdu.writeto('%s/%s_mosaic.linmos.smooth.fits'%(inputs['output_path'],inputs['prefix']))
	hdu.close()
else:
	for i in range(len(ims)):
		lm.makemosaic(images=ims[i], weightimages=pbs[i],weighttype=1,imageweighttype=0)
	exportfits(imagename='%s/%s_mosaic.linmos'%(inputs['output_path'],inputs['prefix']),fitsimage='%s/%s_mosaic.linmos,fits'%(inputs['output_path'],inputs['prefix']),overwrite=True)
	exportfits(imagename='%s/%s_mosaic.weightlinmos'%(inputs['output_path'],inputs['prefix']),fitsimage='%s/%s_mosaic.weightlinmos.fits'%(inputs['output_path'],inputs['prefix']),overwrite=True)
