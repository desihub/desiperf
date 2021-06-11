import pandas as pd
import fnmatch
import numpy as np
import os, glob
import multiprocessing

from astropy.table import Table
from astropy.time import Time
import psycopg2
from datetime import datetime
from bokeh.models import ColumnDataSource


start = '20210'
end = '20210611'
mode = 'update'

fiberpos = pd.read_csv(os.path.join('./data_mgt/fiberpos.csv'))

    conn = psycopg2.connect(host="desi-db", port="5442", database="desi_dev", user="desi_reader", password="reader")
petal_loc_to_id = {0:'4',1:'5',2:'6',3:'3',4:'8',5:'10',6:'11',7:'2',8:'7',9:'9'}

def get_exp_df(start_date, end_date, conn):
    exp_cols = ['id','data_location','targtra','targtdec','skyra','skydec','deltara','deltadec','reqtime','exptime','flavor','program','lead','focus','airmass',
        'mountha','zd','mountaz','domeaz','spectrographs','s2n','transpar','skylevel','zenith','mjd_obs','date_obs','night','moonra','moondec','parallactic','mountel',
        'dome','telescope','tower','hexapod','adc','sequence','obstype']

    exp_df = pd.read_sql_query(f"SELECT * FROM exposure WHERE date_obs >= '{start_date}' AND date_obs < '{end_date}'", conn)

    exp_df_new = exp_df[exp_cols]
    exp_df_new = exp_df_new.rename(columns={'id':'EXPID'})

    exp_df_base = exp_df_new[['EXPID','date_obs']]

    return exp_df_new

def get_telem_data(exp_df_new):
    exp_df_base = exp_df_new[['EXPID','date_obs']]
    dfs = []
    for d in ['telescope','tower','dome']:
        get_keys = True
        i = 0
        while get_keys:
            try:
                t_keys = list(exp_df_new.iloc[i][d].keys())
                get_keys = False
            except:
                i += 1
        dd = {}
        for t in t_keys:
            dd[t] = []
        for item in exp_df_new[d]:
            if item is not None:
                for key in t_keys:
                    try:
                        dd[key].append(item[key])
                    except:
                        dd[key].append(None)
            else:
               for key, l in dd.items():
                    dd[key].append(None)
        df = pd.DataFrame.from_dict(dd)
        dfs.append(df)

    for i, df in enumerate(dfs):
        df.reset_index(inplace=True, drop=True)
        dfs[i] = df
    telem_df = pd.concat(dfs, axis=1)
    telem_df = pd.concat([exp_df_base, telem_df], axis=1)
    return telem_df

def get_coord_data(exp_df_new):
    nights = np.unique(exp_df_new['night'])
    dates = [int(d) for d in nights[np.isfinite(nights)]]

    coord_dir = '/exposures/desi/'
    coord_df = []
    for date in dates:
        coord_files = glob.glob(coord_dir+'{}/*/coordinates-*'.format(date))
        for f in coord_files:
            exposure = int(os.path.splitext(os.path.split(f)[0])[0][-6:])
            try:
                df = Table.read(f, format='fits').to_pandas()
                good = df['OFFSET_0']
                df = df[['PETAL_LOC', 'DEVICE_LOC','TARGET_RA', 'TARGET_DEC','FA_X', 'FA_Y','OFFSET_0','OFFSET_1']]
                df = df.rename(columns={'OFFSET_1':'OFFSET_FINAL','FA_X':'FIBERASSIGN_X','FA_Y':'FIBERASSIGN_Y'})
                df['EXPID'] = exposure
                coord_df.append(df)
            except:
                pass
    coord_df = pd.concat(coord_df)

    return coord_df

def get_fiberpos_data(pos, coord_df):
    init_df = fiberpos[fiberpos.CAN_ID == pos]
    ptl_loc = int(np.unique(init_df.PETAL))
    ptl = petal_loc_to_id[ptl_loc]
    dev = int(np.unique(init_df.DEVICE))
    init_df.drop(['PETAL_LOC','DEVICE_LOC'], axis=1, inplace=True)
    pos_df = pd.merge(coord_df, init_df, how='inner',left_on=['PETAL_LOC','DEVICE_LOC'], right_on=['PETAL','DEVICE'])

    return ptl, dev, pos_df 

def add_posmove_telemetry(ptl, dev, start, end, conn, exp_df_base):
    df = pd.read_sql_query("SELECT * FROM positioner_moves_p{} WHERE device_loc = {} AND time_recorded >= '{}' AND time_recorded < '{}'".format(ptl, dev, start_date,end_date),conn)
    idx = []
    for time in exp_df_base.date_obs:
        ix = np.argmin(np.abs(df['time_recorded'] - time))
        idx.append(ix)
    df = df.iloc[idx]
    df.reset_index(inplace=True, drop=True)
    exp_df_base.reset_index(inplace=True, drop=True)
    pos_telem = pd.concat([exp_df_base, df], axis=1)
    return pos_telem

def save_data(pos, df):
    save_dir = os.path.join(os.environ['DATA_DIR'],'positioners')
    filen = os.path.join(save_dir, '{}.csv'.format(pos))
    if mode == 'new':
        final_df = df
    elif mode == 'update':
        old_df = pd.read_csv(filen)
        for col in list(df.columns):
           if col not in list(old_df.columns):
               try:
                   df.drop(columns=[col], axis=1, inplace=True) 
               except:
                   print(col)
        final_df = pd.concat([old_df, df])

    final_df.to_csv(filen, index=False)

def run(pos):

    exp_df_new = get_exp_df(start_date, end_date, conn)
    exp_df_base = exp_df_new[['EXPID','date_obs']]
    telem_df = get_telem_data(exp_df_new)
    coord_df = get_coord_data(exp_df_new)
    try:
        ptl, dev, pos_df = get_fiberpos_data(pos, coord_df)
        pos_telem = add_posmove_telemetry(ptl, dev, start, end, conn, exp_df_base)
        final_pos_df = pd.merge(pos_df, pos_telem, on=['EXPID'], how='left')
        final_pos_df = pd.merge(final_pos_df, telem_df, on=['EXPID'], how='left')
        save_data(pos, final_pos_df)
        print('Pos {} Done: {}'.format(pos, datetime.now()))
    except:
        print("Issue with {}".format(pos))



if if __name__ == '__main__':

    all_pos = np.unique(fiberpos.CAN_ID) 

    pool = multiprocessing.Pool(processes=64)
    pool.map(run, all_pos)
    pool.terminate()

