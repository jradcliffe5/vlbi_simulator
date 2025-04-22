import pandas as pd
import numpy as np
import os, sys, json

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

try:
	i = sys.argv.index("-c") + 2
except:
	i = 1
	pass

csv_file = sys.argv[i]

if os.path.exists('%s'%csv_file) == False:
    print('ERROR: %s does not exist'%csv_file)

df = pd.read_csv(csv_file,skipinitialspace=True,sep=r',',dtype=str)
master_json = {}
for i in range(len(df)):
    teles = df['telescope'].iloc[i]
    master_json[teles] = {}
    master_json[teles]['ITRF'] = {}
    for j in ['x','y','z']:
        master_json[teles]['ITRF'][j] = df['itrf_%s'%j].iloc[i]
    master_json[teles]['SEFD'] = {}
    for k in (list(df.filter(like='sefd').columns)):
        freq = k.split('_')[-1]
        master_json[teles]['SEFD'][freq] = df[k].iloc[i]
    master_json[teles]['diameter'] = {}
    for k in (list(df.filter(like='diam').columns)):
        freq = k.split('_')[-1]
        master_json[teles]['diameter'][freq] = df[k].iloc[i]
    master_json[teles]['mount'] = df['mount'].iloc[i]

with open('%s.json'%(csv_file.split('.csv')[0]), 'w', encoding='utf-8') as f:
    json.dump(master_json, f, ensure_ascii=False, indent=4, cls=NpEncoder)