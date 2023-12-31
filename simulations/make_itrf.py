import pandas as pd
import sys, json
from simulator_functions import rmfiles, headless, find_frequencies

print('Making configuration files')
inputs=headless(sys.argv[1])
### Antennae used are given in the arguments
antennae = sys.argv[2:]

f = open('%s/simulations/sefds.json'%inputs['repo_path'],)
sefds = json.load(f)
f.close()
f = open('%s/simulations/pbs.json'%inputs['repo_path'],)
diams = json.load(f)
f.close()

sefd_key, obs_freq = find_frequencies(inputs['obs_freq'])

print('Checking antennae for SEFD and diameter compatibility')
ns = []
ni = []
nd = []
for i in antennae:
	try:
		if sefds[sefd_key][i] == -1:
			ns.append(i)
		else:
			pass
	except:
		ni.append(i)
	try:
		if diams[sefd_key][i] == -1:
			nd.append(i)
		else:
			pass
	except:
		pass

if ((ns!=[])|(nd!=[])|(ni!=[])):
	if ns!=[]:
		print('The following antennae have no SEFD information: %s'% ns)
	if nd!=[]:
		print('The following antennae have no primary beam information: %s'% nd)
	if ni!=[]:
		print('The following antennae have no information at all: %s'% ni)
	print('Please modify the pbs.json and sefds.json or remove the antenna')
	sys.exit()


print('Will make configuration file for the following telescopes %s'%antennae)


rmfiles(['sims.itrf'])
## Load VLBI array coordinates
df = pd.read_csv('%s/simulations/master.itrf'%inputs['repo_path'],delimiter=" ", header=None,names=['X', 'Y', 'Z', 'dish_diam', 'station', 'mount'],index_col=False)
## Match and write new sub-configuration
for i in range(len(antennae)):
	if i == 0:
		df3 = df.loc[(df['station'] == antennae[i])].reset_index(drop=True)
	else:
		df3 = df3.append(df.loc[(df['station'] == antennae[i])].reset_index(drop=True),ignore_index=True)
print('Made standard configuration file (sims.itrf)')
df3.to_csv('%s/sims.itrf'%inputs['output_path'],header=False,index=False,sep=' ')

## load vla B-array
rmfiles(['vlapos_sims.itrf'])
df_vla = pd.read_csv('%s/simulations/vlab.itrf'%inputs['repo_path'],delimiter=" ", header=0,names=['X', 'Y', 'Z', 'dish_diam', 'station', 'mount'],index_col=False)
## Replace VLA with VLBI array
for i in range(len(df3)):
	df3['X'][i] = df_vla.iloc[i]['X']
	df3['Y'][i] = df_vla.iloc[i]['Y']
	df3['Z'][i] = df_vla.iloc[i]['Z']
print('Made compressed configuration file (vlapos_sims.itrf) for wide-field imaging')
df3.to_csv('%s/vlapos_sims.itrf'%inputs['output_path'],header=False,index=False,sep=' ')
print('Complete')
