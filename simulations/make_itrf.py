import pandas as pd
import sys, os
from simulator_functions import rmfiles
print('Making configuration files')

### Antennae used are given in the arguments
antennae = sys.argv[1:]

print('Will make configuration file for the following telescopes %s'%antennae)

rmfiles(['sims.itrf'])
## Load VLBI array coordinates
df = pd.read_csv('simulations/master.itrf',delimiter=" ", header=None,names=['X', 'Y', 'Z', 'dish_diam', 'station', 'mount'],index_col=False)
## Match and write new sub-configuration
for i in range(len(antennae)):
	if i == 0:
		df3 = df.loc[(df['station'] == antennae[i])].reset_index(drop=True)
	else:
		df3 = df3.append(df.loc[(df['station'] == antennae[i])].reset_index(drop=True),ignore_index=True)
print('Made standard configuration file (sims.itrf)')
df3.to_csv('sims.itrf',header=False,index=False,sep=' ')

## load vla B-array
rmfiles(['vlapos_sims.itrf'])
df_vla = pd.read_csv('simulations/vlab.itrf',delimiter=" ", header=0,names=['X', 'Y', 'Z', 'dish_diam', 'station', 'mount'],index_col=False)
## Replace VLA with VLBI array
for i in range(len(df3)):
	df3['X'][i] = df_vla.iloc[i]['X']
	df3['Y'][i] = df_vla.iloc[i]['Y']
	df3['Z'][i] = df_vla.iloc[i]['Z']
print('Made compressed configuration file (vlapos_sims.itrf) for wide-field imaging')
df3.to_csv('vlapos_sims.itrf',header=False,index=False,sep=' ')
print('Complete')