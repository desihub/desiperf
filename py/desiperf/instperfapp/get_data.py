
from data_mgt.get_fp_data import FPData 
from data_mgt.get_spec_data import SPECData
from data_mgt.get_pos_data import POSData
import argparse


#start_date = '20201111'
#end_date = '20201218'
start_date = '20200123'
end_date = '20200316'

#fpd = FPData(start_date, end_date, 'update')
#fpd.run()
#specd = SPECData(start_date, end_date, 'update')
#specd.run()
pos = POSData(start_date, end_date, 'new')
pos.run()

