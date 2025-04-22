import casatools
from casatasks import *
import sys, os

from simulator_functions import headless

import logging

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s [%(levelname)s] %(message)s",
	handlers=[
		logging.FileHandler("logs/import_model.log"),
		logging.StreamHandler()
	]
)

## Imports input_file
try:
	i = sys.argv.index("-c") + 2
except:
	i = 1
	pass
part = int(sys.argv[i])
inputs = headless(sys.argv[i+1])

if part == 0:
	exportfits(imagename='%s'%inputs['input_model'],fitsimage='%s-model.fits'%inputs['input_model'])
elif part == 1:
	uvsub(vis='%s.ms'%inputs['prefix'],reverse=True)
elif part == 2:
    split(vis='%s.ms'%inputs['prefix'],outputvis='%s.ms2'%inputs['prefix'])
    os.system('rm -r %s.ms'%(inputs['prefix']))
    os.system('mv %s.ms2 %s.ms'%(inputs['prefix'],inputs['prefix']))
else:
	logger.error('This did not work, please check the errors in CASA to diagnose')
	sys.exit()