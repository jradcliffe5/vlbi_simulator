import re, os, inspect, sys, glob
import numpy as np

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


def headless(inputfile):
	''' Parse the list of inputs given in the specified file. (Modified from evn_funcs.py)'''
	INPUTFILE = open(inputfile, "r")
	control = {}
	# a few useful regular expressions
	newline = re.compile(r'\n')
	space = re.compile(r'\s')
	char = re.compile(r'\w')
	comment = re.compile(r'#.*')
	# parse the input file assuming '=' is used to separate names from values
	for line in INPUTFILE:
		if char.match(line):
			line = comment.sub(r'', line)
			line = line.replace("'", '')
			(param, value) = line.split('=')
			param = newline.sub(r'', param)
			param = param.strip()
			param = space.sub(r'', param)
			value = newline.sub(r'', value)
			value = value.strip()
			valuelist = value.split(',')
			if len(valuelist) == 1:
				if valuelist[0] == '0' or valuelist[0]=='1' or valuelist[0]=='2':
					control[param] = int(valuelist[0])
				else:
					control[param] = str(valuelist[0])
			else:
				control[param] = ','.join(valuelist)
	return control

def write_hpc_headers(step,params):
	func_name = inspect.stack()[0][3]
	print(params)
	hpc_opts = {}
	hpc_opts['job_manager'] = params['job_manager']
	hpc_opts['job_name'] = 'vlbisim_%s'%step
	hpc_opts['email_progress'] = params["email_progress"] 
	hpc_opts['hpc_account'] = params['HPC_project_code']
	hpc_opts['error'] = step

	if ((hpc_opts['job_manager'] == 'pbs')|(hpc_opts['job_manager'] == 'bash')|(hpc_opts['job_manager'] == 'slurm')):
		pass
	#else:
		#sys.exit()

	for i in ['partition','walltime','nodetype','nodes','cpus','mpiprocs','mem']:
		hpc_opts[i] = params['%s'%i]


	hpc_dict = {'slurm':{
					 'partition'     :'#SBATCH --partition=%s'%hpc_opts['partition'],
					 'nodetype'      :'',
					 'cpus'          :'#SBATCH --tasks-per-node %s'%hpc_opts['cpus'], 
					 'nodes'         :'#SBATCH -N %s-%s'%(hpc_opts['nodes'],hpc_opts['nodes']),
					 'mem'           :'#SBATCH --mem=%s'%(hpc_opts['mem']),
					 'mpiprocs'      :'', 
					 'walltime'      :'#SBATCH --time=%s'%hpc_opts['walltime'],
					 'job_name'      :'#SBATCH -J %s'%hpc_opts['job_name'],
					 'hpc_account'   :'#SBATCH --account %s'%hpc_opts['hpc_account'],
					 'email_progress':'#SBATCH --mail-type=BEGIN,END,FAIL\n#SBATCH --mail-user=%s'%hpc_opts['email_progress'],
					 'error':'#SBATCH -o %s%s.sh.stdout.log\n#SBATCH -e %s%s.sh.stderr.log'%(params['output_path'],hpc_opts['error'],params['output_path'],hpc_opts['error'])
					},
				'pbs':{
					 'partition'     :'#PBS -q %s'%hpc_opts['partition'],
					 'nodetype'      :'',
					 'cpus'          :'#PBS -l select=%s:ncpus=%s:mpiprocs=%s:nodetype=%s'%(hpc_opts['nodes'],hpc_opts['cpus'],hpc_opts['mpiprocs'],hpc_opts['nodetype']), 
					 'nodes'         :'',
					 'mem'           :'#PBS -l mem=%s'%(hpc_opts['mem']),
					 'mpiprocs'      :'', 
					 'walltime'      :'#PBS -l walltime=%s'%hpc_opts['walltime'],
					 'job_name'      :'#PBS -N %s'%hpc_opts['job_name'],
					 'hpc_account'   :'#PBS -P %s'%hpc_opts['hpc_account'],
					 'email_progress':'#PBS -m abe -M %s'%hpc_opts['email_progress'],
					 'error':'#PBS -o %s%s.sh.stdout.log\n#PBS -e %s%s.sh.stderr.log'%(params['output_path'],hpc_opts['error'],params['output_path'],hpc_opts['error'])
					},
				'bash':{
					 'partition'     :'',
					 'nodetype'      :'',
					 'cpus'          :'', 
					 'nodes'         :'',
					 'mem'           :'',
					 'mpiprocs'      :'', 
					 'walltime'      :'',
					 'job_name'      :'',
					 'hpc_account'   :'',
					 'email_progress':'',
					 'error':''
					}
				}

	hpc_header= ['#!/bin/bash']

	if step == 'mosaic':
		file = open("%s/mosaic.csv"%params['output_path'], "r")
		nonempty_lines = [line.strip("\n") for line in file if line != "\n"]
		line_count = len(nonempty_lines)
		file.close()
		if params['max_jobs'] == -1:
			tasks = '0-'+str(line_count-1)
		else:
			if (line_count-1) > params['max_jobs']:
				tasks = '0-'+str(line_count-1)+'%'+str(params['max_jobs'])
			else:
				tasks = '0-'+str(line_count-1)
		hpc_dict['slurm']['array_job'] = '#SBATCH --array='+tasks
		hpc_dict['pbs']['array_job'] = '#PBS -t '+tasks
		hpc_dict['bash']['array_job'] = ''
		hpc_opts['array_job'] = -1

	hpc_job = hpc_opts['job_manager']
	for i in hpc_opts.keys():
		if i != 'job_manager':
			if hpc_opts[i] != '':
				if hpc_dict[hpc_opts['job_manager']][i] !='':
					hpc_header.append(hpc_dict[hpc_job][i])


	with open('job_%s.%s'%(step,hpc_job), 'w') as filehandle:
		for listitem in hpc_header:
			filehandle.write('%s\n' % listitem)

def write_job(step,commands,job_manager):
	with open('./job_%s.%s'%(step,job_manager), 'a') as filehandle:
			for listitem in commands:
				filehandle.write('%s\n' % listitem)

def rmfiles(files):
	func_name = inspect.stack()[0][3]
	for i in files:
		if "*" in i:
			files_to_die = glob.glob(i)
			print('Files matching with %s - deleting'% i)
			for j in files_to_die:
				if os.path.exists(j) == True:
					print('File %s found - deleting'% j)
					os.system('rm %s'%j)
				else:
					pass
		elif os.path.exists(i) == True:
			print('File %s found - deleting'% i)
			os.system('rm %s'%i)
		else:
			print('No file found - %s'% i)
	return

def rmdirs(dirs):
	func_name = inspect.stack()[0][3]
	for i in dirs:
		if "*" in i:
			files_to_die = glob.glob(i)
			print('Directories matching with %s - deleting'% i)
			for j in files_to_die:
				if os.path.exists(j) == True:
					print('Directory/table %s found - deleting'% j)
					os.system('rm -r %s'%j)
				else:
					pass
		elif os.path.exists(i) == True:
			print('Directory/table %s found - deleting'% i)
			os.system('rm -r %s'%i)
		else:
			print('No file found - %s'% i)
	return
