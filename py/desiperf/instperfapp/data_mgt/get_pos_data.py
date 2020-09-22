import pandas as pd
import fnmatch
import numpy as np
import os, glob

from astropy.table import Table
from astropy.time import Time
import psycopg2
from datetime import datetime
from bokeh.models import ColumnDataSource


class POSData():
    def __init__(self, start, end):
        self.start_date = start
        self.end_date = end

        self.conn = psycopg2.connect(host="desi-db", port="5442", database="desi_dev", user="desi_reader", password="reader")

        self.FIBERS = [1235 , 2561, 2976, 3881, 4844, 763, 2418, 294, 3532, 4731, 595]

        self.petal_loc_to_id = {0:'4',1:'5',2:'6',3:'3',4:'8',5:'10',6:'11',7:'2',8:'7',9:'9'}

        self.fiberpos = pd.read_csv('./instperfapp//data/fiberpos.csv')

    def get_exp_df(self):
        exp_cols = ['id','data_location','targtra','targtdec','skyra','skydec','deltara','deltadec','reqtime','exptime','flavor','program','lead','focus','airmass',
            'mountha','zd','mountaz','domeaz','spectrographs','s2n','transpar','skylevel','zenith','mjd_obs','date_obs','night','moonra','moondec','parallactic','mountel',
            'dome','telescope','tower','hexapod','adc','sequence','obstype']

        exp_df = pd.read_sql_query(f"SELECT * FROM exposure WHERE date_obs >= '{self.start_date}' AND date_obs < '{self.end_date}'", self.conn)

        exp_df_new = exp_df[exp_cols]
        self.exp_df_new = exp_df_new.rename(columns={'id':'EXPID'})

        self.exp_df_base = self.exp_df_new[['EXPID','date_obs']]

    def get_fiberpos_data(self, fib):
        init_df = self.fiberpos[self.fiberpos.FIBER == fib]
        self.ptl_loc = int(np.unique(init_df.PETAL_LOC))
        self.ptl = self.petal_loc_to_id[self.ptl_loc]
        self.dev = int(np.unique(init_df.DEVICE_LOC))
        self.pos_df = pd.merge(self.coord_df, init_df, how='left',left_on=['PETAL_LOC','DEVICE_LOC'], right_on=['PETAL','DEVICE'])


    def add_posmove_telemetry(self, fib):
        
        df = pd.read_sql_query("SELECT * FROM positioner_moves_p{} WHERE device_loc = {} AND time_recorded >= '{}' AND time_recorded < '{}'".format(self.ptl, self.dev, self.start_date, self.end_date),self.conn)
        idx = []
        for time in self.exp_df_base.date_obs:
            ix = np.argmin(np.abs(df['time_recorded'] - time))
            idx.append(ix)
        df = df.iloc[idx]
        self.pos_telem = pd.concat([self.exp_df_base, df], axis=1)


    def get_coord_data(self):
        nights = np.unique(self.exp_df_new['night'])
        dates = [int(d) for d in nights[np.isfinite(nights)]]

        coord_dir = '/exposures/desi/'
        self.coord_df = []
        for date in dates:
            coord_files = glob.glob(coord_dir+'{}/*/coordinates-*'.format(date))
            for f in coord_files:
                exposure = int(os.path.splitext(os.path.split(f)[0])[0][-6:])
                try:
                    df = Table.read(f, format='fits').to_pandas()
                    good = df['OFFSET_0']
                    final_move = np.sort(fnmatch.filter(df.columns, 'OFFSET_*'))[-1]
                    df = df[['PETAL_LOC', 'DEVICE_LOC','TARGET_RA', 'TARGET_DEC','FIBERASSIGN_X', 'FIBERASSIGN_Y','OFFSET_0',final_move,'FIBER']]
                    df = df.rename(columns={final_move:'OFFSET_FINAL'})
                    df['EXPID'] = exposure
                    self.coord_df(df)
                except:
                    pass
        self.coord_df = pd.concat(self.coord_df)


    def run(self):
        print('Start: {}'.format(datetime.now()))
        self.get_exp_df()
        print('Exp: {}'.format(datetime.now()))
        self.get_coord_data()
        print('Coord: {}'.format(datetime.now()))
        for fib in self.FIBERS:
            self.get_fiberpos_data(fib)
            self.add_posmove_telemetry(fib)
            self.final_fib_df = pd.merge(self.pos_df, self.pos_telem, on=['EXPID'], how='left')
            print('Fib {} Done: {}'.format(fib, datetime.now()))
            self.final_fib_df.to_csv('{}.csv'.format(fib), index=False) 

