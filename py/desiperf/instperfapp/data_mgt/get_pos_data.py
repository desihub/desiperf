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
    def __init__(self, start, end, mode):
        self.mode = mode #new, update
        self.start_date = start
        self.end_date = end
        self.save_dir = os.path.join(os.environ['DATA_DIR'],'positioners')
        self.fiberpos = pd.read_csv(os.path.join(os.environ['DATA_DIR'],'fiberpos.csv'))

        self.conn = psycopg2.connect(host="desi-db", port="5442", database="desi_dev", user="desi_reader", password="reader")

        #self.FIBERS = [1235 , 2561, 2976, 3881, 4844, 763, 2418, 294, 3532, 4731, 595]
        all_pos = np.unique(self.fiberpos.CAN_ID) 
        
        done_pos =  [int(os.path.splitext(f)[0]) for f in os.listdir(self.save_dir)]
        self.POSITIONERS = [pos for pos in all_pos if pos not in done_pos]
        print(self.POSITIONERS)
        #self.POSITIONERS = [6205, 6828, 4804, 4946, 6830, 4374, 3770, 7403, 3239, 7545, 3963]

        self.petal_loc_to_id = {0:'4',1:'5',2:'6',3:'3',4:'8',5:'10',6:'11',7:'2',8:'7',9:'9'}

        self.fiberpos = pd.read_csv('./data/fiberpos.csv')


    def get_exp_df(self):
        exp_cols = ['id','data_location','targtra','targtdec','skyra','skydec','deltara','deltadec','reqtime','exptime','flavor','program','lead','focus','airmass',
            'mountha','zd','mountaz','domeaz','spectrographs','s2n','transpar','skylevel','zenith','mjd_obs','date_obs','night','moonra','moondec','parallactic','mountel',
            'dome','telescope','tower','hexapod','adc','sequence','obstype']

        exp_df = pd.read_sql_query(f"SELECT * FROM exposure WHERE date_obs >= '{self.start_date}' AND date_obs < '{self.end_date}'", self.conn)

        exp_df_new = exp_df[exp_cols]
        self.exp_df_new = exp_df_new.rename(columns={'id':'EXPID'})

        self.exp_df_base = self.exp_df_new[['EXPID','date_obs']]

    def get_fiberpos_data(self, pos):
        init_df = self.fiberpos[self.fiberpos.CAN_ID == pos]
        self.ptl_loc = int(np.unique(init_df.PETAL))
        self.ptl = self.petal_loc_to_id[self.ptl_loc]
        self.dev = int(np.unique(init_df.DEVICE))
        init_df.drop(['PETAL_LOC','DEVICE_LOC'], axis=1, inplace=True)
        self.pos_df = pd.merge(self.coord_df, init_df, how='inner',left_on=['PETAL_LOC','DEVICE_LOC'], right_on=['PETAL','DEVICE'])

    def add_posmove_telemetry(self):
        df = pd.read_sql_query("SELECT * FROM positioner_moves_p{} WHERE device_loc = {} AND time_recorded >= '{}' AND time_recorded < '{}'".format(self.ptl, self.dev, self.start_date, self.end_date),self.conn)
        idx = []
        for time in self.exp_df_base.date_obs:
            ix = np.argmin(np.abs(df['time_recorded'] - time))
            idx.append(ix)
        df = df.iloc[idx]
        df.reset_index(inplace=True, drop=True)
        self.exp_df_base.reset_index(inplace=True, drop=True)
        self.pos_telem = pd.concat([self.exp_df_base, df], axis=1)

    def get_telem_data(self):
        dfs = []
        for d in ['telescope','tower','dome']:
            try:
                t_keys = list(self.exp_df_new.iloc[0][d].keys())
            except:
                t_keys = list(self.exp_df_new.iloc[2][d].keys())
            dd = {}
            for t in t_keys:
                dd[t] = []
            for item in self.exp_df_new[d]:
                if item is not None:
                    for key, val in item.items():
                        dd[key].append(val)
                else:
                    for key, l in dd.items():
                        dd[key].append(val)
            df = pd.DataFrame.from_dict(dd)
            dfs.append(df)

        for i, df in enumerate(dfs):
            df.reset_index(inplace=True, drop=True)
            dfs[i] = df
        telem_df = pd.concat(dfs, axis=1)
        self.telem_df = pd.concat([self.exp_df_base, telem_df], axis=1)

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
                    if int(final_move[-1]) > 0:
                        df = df[['PETAL_LOC', 'DEVICE_LOC','TARGET_RA', 'TARGET_DEC','FIBERASSIGN_X', 'FIBERASSIGN_Y','OFFSET_0',final_move]]
                        df = df.rename(columns={final_move:'OFFSET_FINAL'})
                        df['EXPID'] = exposure
                        self.coord_df.append(df)
                    else:
                        print(f, final_move)
                except:
                    pass
        self.coord_df = pd.concat(self.coord_df)

    def save_data(self, pos, df):
        filen = os.path.join(self.save_dir, '{}.csv'.format(pos))
        if self.mode == 'new':
            final_df = df
        elif self.mode == 'update':
            old_df = pd.read_csv(filen)
            for col in list(df.columns):
               if col not in list(old_df.columns):
                   try:
                       df.drop(columns=[col], axis=1, inplace=True) 
                   except:
                       print(col)
            final_df = pd.concat([old_df, df])

        final_df.to_csv(filen, index=False)

    def run(self):
        print('Start: {}'.format(datetime.now()))
        self.get_exp_df()
        print('Exp: {}'.format(datetime.now()))
        self.get_telem_data()
        print('Telem: {}'.format(datetime.now()))
        self.get_coord_data()
        print('Coord: {}'.format(datetime.now()))
        for pos in self.POSITIONERS:
            try:
                self.get_fiberpos_data(pos)
                self.add_posmove_telemetry()
                final_pos_df = pd.merge(self.pos_df, self.pos_telem, on=['EXPID'], how='left')
                #final_pos_df = pd.merge(final_pos_df, self.exp_df_new, on=['EXPID'], how='left')
                self.final_pos_df = pd.merge(final_pos_df, self.telem_df, on=['EXPID'], how='left')
                self.save_data(pos, self.final_pos_df)
                print('Pos {} Done: {}'.format(pos, datetime.now()))
            #self.final_pos_df.to_csv(self.save_dir+'{}.csv'.format(pos), index=False) 
            except:
                print("Issue with {}".format(pos))

