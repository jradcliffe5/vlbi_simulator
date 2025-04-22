import pandas as pd
import sys, json
from simulator_functions import rmfiles, headless, find_frequencies
import logging

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s [%(levelname)s] %(message)s",
	handlers=[
		logging.FileHandler("logs/make_itrf.log"),
		logging.StreamHandler()
	]
)

logging.info('Making configuration files')
inputs=headless(sys.argv[1])
### Antennae used are given in the arguments
antennae = sys.argv[2:]

f = open('%s/simulations/ant_info.json'%inputs['repo_path'],)
ant_info = json.load(f)
f.close()

sefd_key, obs_freq = find_frequencies(inputs['obs_freq'])

logging.info('Checking antenna data')
ns = []
ni = []
nd = []
nm = []
nitrf = []
for i in antennae:
	try:
		if ant_info[i]['SEFD'][sefd_key] == -1:
			ns.append(i)
		else:
			pass
	except:
		ni.append(i)
	try:
		if ant_info[i]['diameter'][sefd_key] == -1:
			nd.append(i)
		else:
			pass
	except:
		pass
	try:
		if ant_info[i]['mount'] == -1:
			nm.append(i)
		else:
			pass
	except:
		pass
	try:
		if ((ant_info[i]['ITRF']['x'] == -1) or (ant_info[i]['ITRF']['y'] == -1) or (ant_info[i]['ITRF']['z'] == -1)):
			nitrf.append(i)
		else:
			pass
	except:
		pass

if ((nitrf!=[]) or (nm!=[]) or (ns!=[]) or (nd!=[]) or (ni!=[])):
	if ni!=[]:
		logging.error('The following antennae have no information at all: %s'% ni)
	if nitrf!=[]:
		logging.error('The following antennas have no ITRF coordinates: %s'% nitrf)
	if nm!=[]:
		logging.error('The following antennas have no mount information: %s'% nm)
	if ns!=[]:
		logging.error('The following antennas have no SEFD information: %s'% ns)
	if nd!=[]:
		logging.error('The following antennas have no primary beam information: %s'% nd)
	logging.error('Please modify the ant_info.json or remove the antenna')
	sys.exit()


logging.info('Will make configuration file for the following telescopes %s'%antennae)


rmfiles(['sims.itrf'])
## Load VLBI array coordinates
if (inputs['mode'] == "ms_only") or (inputs['mode'] == "ms_image"):
	df3 = pd.DataFrame(columns=['X', 'Y', 'Z', 'dish_diam', 'station', 'mount'])
	## Match and write new sub-configuration
	for i in antennae:
		df3 = df3.append({'X':ant_info[i]['ITRF']['x'],
						'Y':ant_info[i]['ITRF']['y'],
						'Z':ant_info[i]['ITRF']['z'],
						'dish_diam':ant_info[i]['diameter'][sefd_key],
						'station':i,
						'mount':ant_info[i]['mount']},ignore_index=True)

	logging.info('Made standard configuration file (sims.itrf)')
	df3.to_csv('%s/sims.itrf'%inputs['output_path'],header=False,index=False,sep=' ')
## load vla B-array
elif (inputs['mode'] == "rms_maps"):
	rmfiles(['vlapos_sims.itrf'])
	df_vla = pd.read_csv('%s/simulations/vlab.itrf'%inputs['repo_path'],delimiter=" ", header=0,names=['X', 'Y', 'Z', 'dish_diam', 'station', 'mount'],index_col=False)
	## Replace VLA with VLBI array
	for i in range(len(df3)):
		df3['X'][i] = df_vla.iloc[i]['X']
		df3['Y'][i] = df_vla.iloc[i]['Y']
		df3['Z'][i] = df_vla.iloc[i]['Z']
	logging.info('Made compressed configuration file (vlapos_sims.itrf) for wide-field imaging')
	df3.to_csv('%s/vlapos_sims.itrf'%inputs['output_path'],header=False,index=False,sep=' ')
else:
	logging.error('Mode selected is wrong, please correct')
	sys.exit()
logging.info('Complete - array configuration information has been built')