from data_mgt.data_handler import DataHandler 
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--option','-o',help='Option for getting data',choices=('no_update','init','update'))

args = parser.parse_args()
print(args)
option = args.option

DH = DataHandler(option=option)
DH.run()
