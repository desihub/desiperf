"""
Get Positioner data
"""

import data_mgt.get_pos_data 
import argparse
from itertools import repeat
import os
import pandas as pd
import numpy as np
from datetime import datetime
import multiprocessing

#os.environ['DATA_DIR'] = '/global/cscratch1/sd/parkerf/data_local'
#os.environ['DATA_MGT_DIR'] = '/global/homes/p/parkerf/InstPerf/desiperf/py/desiperf/instperfapp/data_mgt'
fiberpos = pd.read_csv(os.path.join(os.environ['DATA_MGT_DIR'],'fiberpos.csv'))

parser = argparse.ArgumentParser(description='Update Positioner data')
parser.add_argument('start', help='start date')
parser.add_argument('end', help='end date')
parser.add_argument('-o','--option', help='option: new, update (default)', default = 'update')
parser.add_argument("-p", "--positioners", help = 'List of positioners')

args = parser.parse_args()

start_date = args.start
end_date = args.end
option = args.option
print(option)
positioners = args.positioners
print(positioners)
if positioners is None:
    all_pos = np.unique(fiberpos.CAN_ID)
else:
    all_pos = positioners

#finished = pd.read_csv('/n/home/desiobserver/parkerf/desiperf/py/desiperf/data_local/positioners/finished.txt',header=None)
#fin = list(finished[0])[:-1]
#finished_pos = [int(os.path.splitext(os.path.split(f)[1])[0]) for f in fin]
#print(finished_pos)
#all_pos = [x for x in all_pos if x not in finished_pos]

print('Running for {} positioners'.format(len(all_pos)))

start_time = datetime.now()

exp_df_base, telem_df, coord_df, ptl_dbs  = data_mgt.get_pos_data.get_dfs(start_date, end_date)

pool = multiprocessing.Pool(processes=64)
pool.starmap(data_mgt.get_pos_data.run, zip(all_pos, repeat(start_date), repeat(end_date), repeat(exp_df_base), repeat(coord_df), repeat(telem_df), repeat(fiberpos), repeat(ptl_dbs), repeat(option)))
pool.terminate()
print("total time: ",(datetime.now()-start_time).total_seconds()/60.)
