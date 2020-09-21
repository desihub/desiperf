
from data_mgt.get_fp_data import FPData 
from data_mgt.get_spec_data import SPECData
import argparse


start_date = '20200121'
end_date = '20200317'

fpd = FPData(start_date, end_date)
fpd.run()
#specd = SPECData(start_date, end_date)
#specd.run()

