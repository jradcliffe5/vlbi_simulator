import inspect, os, sys, json, ast
import copy
## Python 2 will need to adjust for casa 6
import collections

filename = inspect.getframeinfo(inspect.currentframe()).filename
sys.path.append(os.path.dirname(os.path.realpath(filename)))
sys.path.append(os.path.dirname(os.path.realpath(filename))+"/simulations")

from simulator_functions import *

## Imports input_file
try:
	i = sys.argv.index("-c") + 2
except:
	i = 1
	pass

## Load global inputs
inputs = headless(sys.argv[i])
adv_inputs = headless(sys.argv[i+1])
part = int(sys.argv[i+2])

rpath=inputs['repo_path']

## Set the parameters for the HPC resources
params = {}
params['job_manager'] = str(inputs['job_manager'])
params['email_progress'] = str(inputs['email_progress'])
params['HPC_project_code'] = str(inputs['HPC_project_code'])
params['partition'] = str(inputs['partition'])
params['walltime'] = str(inputs['walltime'])
params['nodetype'] = str(inputs['nodetype'])
params['nodes'] = int(inputs['nodes'])
params['cpus'] = int(inputs['cpus'])
params['mpiprocs'] = int(inputs['mpiprocs'])
params['output_path'] = inputs['output_path']
params['mem'] = inputs['mem']
params['max_jobs'] = int(inputs['max_jobs'])

## Generate single pointing to fit beam
if part == 1:
	commands = []
	step = 'make_ms'
	write_hpc_headers(step,params)
	ms = '%s/%s.ms'%(inputs['output_path'],inputs['prefix'])

	## Generate itrfs
	antennae = ast.literal_eval(inputs['antennae'])
	commands.append('%s %s/simulations/make_itrf.py %s %s'%(inputs['CASA_exec'], rpath, sys.argv[i]," ".join(antennae)))

	## Generate measurement set
	commands.append('%s %s/simulations/make_measurement_set.py S %s %s'%(inputs['stimela_exec'],rpath, sys.argv[i], sys.argv[i+1]))

	## Add noise to measurement sets & flag
	commands.append('%s %s/simulations/add_noise_hetero.py S %s %s'%(inputs['CASA_exec'],rpath, sys.argv[i], sys.argv[i+1]))

	if inputs['input_model'] != '':
		if inputs['input_model'].endswith('.fits'):
			commands.append('cp %s %s-model.fits'%(inputs['input_model'],inputs['input_model'].split('.fits')[0]))
			modelprefix='%s'%inputs['input_model'].split('.fits')[0]
		else:
			commands.append('%s %s/simulations/input_model.py 0 %s' % (inputs['CASA_exec'], rpath, sys.argv[i]))
			modelprefix='%s'%inputs['input_model']
		commands.append('%s -predict -name %s %s/%s.ms'%(inputs['wsclean_exec'], modelprefix, inputs['output_path'], inputs['prefix']))
		commands.append('%s %s/simulations/input_model.py 1 %s' % (inputs['CASA_exec'], rpath, sys.argv[i]))
	commands.append('%s %s/simulations/input_model.py 2 %s' % (inputs['CASA_exec'], rpath, sys.argv[i]))
	
	write_job(step=step,commands=commands,job_manager=inputs['job_manager'])

if part == 2:
	commands = []
	step = 'single_pointing_pb'
	write_hpc_headers(step,params)
	## Generate a terms
	commands.append('%s %s/simulations/generate_pb_aterms.py 0 0 0 S %s %s' %(inputs['CASA_exec'], rpath, sys.argv[i], sys.argv[i+1]))

	## Wsclean primary beam
	commands.append('%s -name %s/%s -no-update-model-required --aterm-kernel-size 157 -weight %s -scale %s -niter 1 -mgain 0.9 -auto-threshold 0.5 -auto-mask 4 -use-idg -idg-mode hybrid -aterm-config %s.ms_aterm_norotate_config.txt -size %d %d %s/%s.ms'%(inputs['wsclean_exec'],inputs['output_path'],inputs['prefix'],inputs['weight'],inputs['cell'],inputs['prefix'],int(inputs['size']),int(inputs['size']),inputs['output_path'],inputs['prefix']))

	if inputs['mosaic'] == "False":
		commands.append('%s %s/%s-image-pb.fits'%(inputs['rms_exec'],inputs['output_path'],inputs['prefix']))
	else:
		commands.append('%s %s/simulations/fit_pb.py %s'%(inputs['CASA_exec'],rpath, sys.argv[i]))
		commands.append('%s %s/simulations/generate_mosaic_pointings.py %s'%(inputs['CASA_exec'],rpath,sys.argv[i]))
		commands.append('%s %s/simulations/make_measurement_set.py M %s %s'%(inputs['stimela_exec'],rpath, sys.argv[i], sys.argv[i+1]))

	write_job(step=step,commands=commands,job_manager=inputs['job_manager'])

if part == 3:
	if inputs['mosaic'] == "True":
		commands = []
		step = 'mosaic'
		write_hpc_headers(step,params)

		commands.append('array=($(ls -d %s/%s_mosaic_*.ms | sort -V))'%(inputs['output_path'],inputs['prefix']))
		commands.append('len=${#array[@]}')
		commands.append('a=$SLURM_ARRAY_TASK_ID')
		## Add noise to all ms
		commands.append('%s %s/simulations/add_noise_hetero.py M$a %s %s'%(inputs['CASA_exec'],rpath, sys.argv[i], sys.argv[i+1]))

		## Make all a terms
		commands.append('%s %s/simulations/generate_pb_aterms.py 0 0 0 M$a %s %s'%(inputs['CASA_exec'], rpath, sys.argv[i], sys.argv[i+1]))

		## Unzip a terms
		#commands.append('gunzip -f ${array[$a]}\"_pb_flat_norotate.fits.gz\"')

		## Make images
		commands.append('%s -name %s/${array[$a]}_IM -no-update-model-required --aterm-kernel-size 157 -weight %s -scale %s -niter 1 -mgain 0.9 -auto-threshold 0.5 -auto-mask 4 -use-idg -idg-mode hybrid -aterm-config ${array[$a]}_aterm_norotate_config.txt -size %d %d ${array[$a]}'%(inputs['wsclean_exec'],inputs['output_path'],inputs['weight'],inputs['cell'],int(inputs['size']),int(inputs['size'])))

		## Convert to casa ims
		commands.append('%s %s/simulations/convert_fits_to_casa.py ${array[$a]}'%(inputs['CASA_exec'],rpath))

		write_job(step=step,commands=commands,job_manager=inputs['job_manager'])
		
		commands = []
		step = 'make_image'
		write_hpc_headers(step,params)

		## Make mosaic
		commands.append('%s %s/simulations/make_mosaic.py %s'%(inputs['CASA_exec'],rpath,sys.argv[i]))

		## Make rms map
		commands.append('%s %s/%s_mosaic.linmos.fits'%(inputs['rms_exec'],inputs['output_path'],inputs['prefix']))

		write_job(step=step,commands=commands,job_manager=inputs['job_manager'])
