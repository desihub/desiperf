"""
Get Focalplane and Spectrograph data
"""

from data_mgt.get_fp_data import FPData 
from data_mgt.get_spec_data import SPECData
import argparse
import os
from datetime import datetime

#os.environ['DATA_DIR'] = '/global/cscratch1/sd/parkerf/data_local'

parser = argparse.ArgumentParser(description='Update Focalplane and Spectrograph data')
parser.add_argument('start', help='start date')
parser.add_argument('end', help='end date')
parser.add_argument('-o','--option', help='option: new, update (default)', default = 'update')
parser.add_argument("-f", "--focalplane", action="store_true", help = 'Focal plane data only')
parser.add_argument("-s", "--spectrograph", action="store_true", help = 'Spectrograph data only')

args = parser.parse_args()

start_date = args.start
end_date = args.end
option = args.option
fp_only = args.focalplane
spec_only = args.spectrograph

start_time = datetime.now()
if fp_only:
    fpd = FPData(start_date, end_date, option)
    fpd.run()
elif spec_only:
    specd = SPECData(start_date, end_date, option)
    specd.run()
else:
    fpd = FPData(start_date, end_date, option)
    fpd.run()
    specd = SPECData(start_date, end_date, option)
    specd.run()

print("Total time: ",(datetime.now()-start_time).total_seconds()/60.)

