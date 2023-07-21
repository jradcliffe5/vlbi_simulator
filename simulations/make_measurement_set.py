from simms import simms
import os, glob, sys, ast
import numpy as np
from datetime import datetime, timedelta
from simulator_functions import headless, rmdirs, rmfiles
import sys
def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

def find_frequencies(obs_freq):
	freq_c = {"92cm":0.325861,
	   "49cm":0.611821,
	   "UHF":1.0,
	   "21cm":1.427583,
	   "18cm":1.665513,
	   "13cm":2.306096,
	   "6cm":4.996541,
	   "5cm":5.99584916,
	   "4cm":7.49481145,
	   "2cm":14.9896229,
	   "13mm":23.060958,
	   "9mm":33.310273,
	   "7mm":42.827494,
	   "3mm":99.930819,
	   "2mm":149.896229}
	try:
		obs_freq=float(obs_freq) ## try to see if obs frequency is a float
		key_list = list(freq_c.keys())
		val_list = list(freq_c.values())
		val = find_nearest(val_list,obs_freq)
		position = val_list.index(val)
		sefd_key=key_list[position]
	except:
		try:
			sefd_key = obs_freq
			obs_freq=freq_c[obs_freq]
		except:
			print('Observing frequency incorrect')
			sys.exit()
	return sefd_key, obs_freq

try:
	i = sys.argv.index("-c") + 2
except:
	i = 1
	pass

## Import inputs
inputs = headless(sys.argv[i+1])
adv_inputs = headless(sys.argv[i+2])
output = str(inputs['output_path'])
try:
	prefix = str(inputs['prefix'])
except:
	print('Inputs not set, will default to sim')
	prefix='sim'

## Calculate bandwidths from datarates or directly
# First get datarates - bandwidth = datarate/npols/nbits/2
data_rate = float(inputs['data_rate'])
npols = float(inputs['npols'])
bits = float(inputs['bit_sampling'])
sefdkey, obs_freq = find_frequencies(inputs['obs_freq'])
print(sefdkey,obs_freq)
if npols >=2.:
	pols = 2.
	if npols == 4.:
		stokes ='RR RL LR LL'
	else:
		stokes='RR LL'
else:
	pols = 1.
	stokes = 'RR'
# Try to find bandwidth in MHz from input file else calculate data rate bw
try: 
	bw = float(inputs['bandwidth'])
except:
	bw = data_rate/pols/bits/2.
# Set low end of the frequency in GHz

freq0 = obs_freq-(bw/2000.)

## Get data formatting to control size
nchan= int(adv_inputs['nchan'])
int_time = np.round(float(adv_inputs['int_time']),5)

## Set up time on source, 12 hours used for mosaic simulations so an accurate primary beam can be inferred.
if inputs['mosaic'] == "True":
	tos = 12
else:
	tos = float(inputs['total_time_on_source'])

## If making very wide-field images, we simply use vla-c array positions so we don't need to make massive images.
if str(inputs['wf_ITRF']) == 'True':
	itrf="%s/vlapos_sims.itrf"%output
else:
	itrf="%s/sims.itrf"%output

## Determine the pointing centre from field centre which should be also in casa format
pointing_centre = ast.literal_eval(inputs['field_centre'])

## Single pointing simms command
if sys.argv[i] == 'S':
	# Delete ms if it exists and MS variable
	rmdirs(['%s/%s.ms'%(output,prefix)])
	MS='%s/%s.ms'%(output,prefix)

	# Round the time on source as that was causing splits in scan lengths
	tos = np.round(tos,5)

	# Simms command
	print('Making single pointing ms - %s.ms with the following parameters'%prefix)
	print('Total time on source: %.2f hr, integration time = %.2f s'%(tos,int_time))
	print('Bandwidth: %.6f MHz, number channels: %d'%(bw,nchan))
	simms.create_empty_ms(
	msname=MS,
	label=None,
	tel="EVN", # Set telescope name, doesn't matter at all really.
	pos=itrf, # Put in itrf file
	pos_type='ascii',
	ra=pointing_centre[0],
	dec=pointing_centre[1],
	synthesis=tos,
	scan_length=[tos],
	dtime=int_time,
	freq0="%.8fGHz"%freq0,
	dfreq="%.8fMHz"%(bw/np.round(float(nchan),5)),
	nchan="%d"%nchan,
	stokes=stokes,
	setlimits=False,
	elevation_limit=0,
	shadow_limit=0,
	outdir="./",
	nolog=False,
	coords='itrf',
	lon_lat=None,
	noup=False,
	nbands=1,
	direction=[],
	date=None,
	fromknown=False,
	feed='perfect R L',
	scan_lag=0,
	auto_corr=False,
	optimise_start=None
	)
elif sys.argv[1] == 'M':
	with open('%s/mosaic.csv'%inputs['output_path']) as f:
		lines = f.readlines()
	direction = []
	for i in lines:
		if not i.startswith('#'):
			line = i.split(" ")
			direction.append([line[2],line[4]])
	tos = float(inputs['total_time_on_source'])
	total_time = tos
	print(total_time, total_time/float(len(direction)) , len(direction))
	synthesis = np.round(total_time/float(len(direction)),5)
	for i in range(len(direction)):
		print('Making %s_mosaic_%s.ms with direction ra=%s, dec=%s'%(prefix,i,direction[i][0],direction[i][1]))
		rmdirs(['%s/%s_mosaic_%s.ms'%(output, prefix, i)])
		MS='%s/%s_mosaic_%s.ms'%(output, prefix, i)
		dt = datetime.strptime(adv_inputs['time_start'], '%d %b %Y') #+ timedelta(hours=2/60+(0*total_time/float(len(direction))))
		simms.create_empty_ms(
		msname=MS,
		label=None,
		tel="EVN",
		pos=itrf,
		pos_type='ascii',
		ra=direction[i][0],
		dec=direction[i][1],
		direction=None,
		synthesis=synthesis,
		scan_length=[synthesis],
		dtime=int_time,
		freq0="%.8fGHz"%freq0,
		dfreq="%.8fMHz"%(bw/np.round(float(nchan),5)),
		nchan="%d"%nchan,
		stokes=stokes,
		setlimits=False,
		elevation_limit=0,
		shadow_limit=0,
		outdir="./",
		nolog=False,
		coords='itrf',
		lon_lat=None,
		noup=False,
		nbands=1,
		date=None,
		fromknown=False,
		feed='perfect R L',
		scan_lag=0,
		auto_corr=False,
		optimise_start=None
		)
else:
	print('Something has gone wrong')
	sys.exit()