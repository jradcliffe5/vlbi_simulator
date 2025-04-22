import json
import pandas as pd
import numpy as np
f = open('sefds.json',)
sefds = json.load(f)
f.close()
f = open('pbs.json',)
diams = json.load(f)
f.close()
df = pd.read_csv('master.itrf',delimiter=" ", header=None,names=['X', 'Y', 'Z', 'dish_diam', 'station', 'mount'],index_col=False)
pd.set_option("display.precision",10)
ant_names = list(sefds["18cm"].keys())
freqs = list(sefds.keys())


master_json = {}
for i,j in enumerate(ant_names):
	master_json[j] = {}
	master_json[j]['ITRF'] = {}
	master_json[j]['SEFD'] = {}
	master_json[j]['diameter'] = {}
	try:
		master_json[j]['ITRF']['x'] = df['X'][np.where(df['station']==j)[0]].values[0]
		master_json[j]['ITRF']['y'] = df['Y'][np.where(df['station']==j)[0]].values[0]
		master_json[j]['ITRF']['z'] = df['Z'][np.where(df['station']==j)[0]].values[0]
	except:
		master_json[j]['ITRF']['x'] = -1
		master_json[j]['ITRF']['y'] = -1
		master_json[j]['ITRF']['z'] = -1
	try:
		master_json[j]['mount'] = df['mount'][np.where(df['station']==j)[0]].values[0]
	except:
		master_json[j]['mount'] = -1
	
	for k,m in enumerate(freqs):
		try:
			master_json[j]['SEFD'][m] = sefds[m][j]
		except:
			master_json[j]['SEFD'][m] = -1
		try:
			master_json[j]['diameter'][m] = diams[m][j]
		except:
			master_json[j]['diameter'][m] = -1

#for k,m in enumerate(freqs):
with open('ant_info.json', 'w', encoding='utf-8') as f:
    json.dump(master_json, f, ensure_ascii=False, indent=4)