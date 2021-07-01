import pandas as pd
import fnmatch
import numpy as np
import os, glob


from astropy.table import Table
from astropy.time import Time
import psycopg2
#from psycopg2 import pool
from datetime import datetime
from bokeh.models import ColumnDataSource


conn = psycopg2.connect(host="db.replicator.dev-cattle.stable.spin.nersc.org", port="60042", database="desi_dev", user="desi_reader", password="reader")
petal_loc_to_id = {0:'4',1:'5',2:'6',3:'3',4:'8',5:'10',6:'11',7:'2',8:'7',9:'9'}


def get_dfs(start, end):
    exp_cols = ['id','data_location','targtra','targtdec','skyra','skydec','deltara','deltadec','reqtime','exptime','flavor','program','lead','focus','airmass',  'mountha','zd','mountaz','domeaz','spectrographs','s2n','transpar','skylevel','zenith','mjd_obs','date_obs','night','moonra','moondec','parallactic','mountel','dome','telescope','tower','hexapod','adc','sequence','obstype']
    exp_df = pd.read_sql_query("SELECT * FROM exposure WHERE date_obs >= '{}' AND date_obs < '{}'".format(start, end), conn)
    exp_df_new = exp_df[exp_cols]
    exp_df_new = exp_df_new.rename(columns={'id':'EXPID'})
    exp_df_base = exp_df_new[['EXPID','date_obs']]

    print('get telem data')
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

    print('get_coord_data')
    nights = np.unique(exp_df_new['night'])
    dates = [int(d) for d in nights[np.isfinite(nights)]]

    coord_dir = '/global/cfs/cdirs/desi/spectro/data/'
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
    print('done with dfs')
    
    ptl_dbs = {}
    for ptl in petal_loc_to_id.values():
        print('Getting data for Petal {}'.format(ptl))
        ptl_dbs[ptl] = pd.read_sql_query("SELECT * FROM positioner_moves_p{} WHERE time_recorded >= '{}' AND time_recorded < '{}'".format(ptl, start,end),conn)
        
    return exp_df_base, telem_df, coord_df, ptl_dbs 


def get_fiberpos_data(pos, coord_df, fiberpos):
    init_df = fiberpos[fiberpos.CAN_ID == pos]
    ptl_loc = int(np.unique(init_df.PETAL))
    ptl = petal_loc_to_id[ptl_loc]
    dev = int(np.unique(init_df.DEVICE))
    init_df.drop(['PETAL_LOC','DEVICE_LOC'], axis=1, inplace=True)
    pos_df = pd.merge(coord_df, init_df, how='inner',left_on=['PETAL_LOC','DEVICE_LOC'], right_on=['PETAL','DEVICE'])

    return ptl, dev, pos_df 

def add_posmove_telemetry(ptl, dev, start, end,  exp_df_base, ptl_dbs):
    df = ptl_dbs[ptl]
    df = df[df.device_loc == dev]
    idx = []
    for time in exp_df_base.date_obs:
        ix = np.argmin(np.abs(df['time_recorded'] - time))
        idx.append(ix)
    df = df.iloc[idx]
    df.reset_index(inplace=True, drop=True)
    exp_df_base.reset_index(inplace=True, drop=True)
    pos_telem = pd.concat([exp_df_base, df], axis=1)
    return pos_telem

def save_data(pos, df, mode):
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
                    pass
                    #print(col)
        final_df = pd.concat([old_df, df])

    final_df.to_csv(filen, index=False)

def run(pos, start, end, exp_df_base, coord_df, telem_df, fiberpos, ptl_dbs, mode):
    try:
        ptl, dev, pos_df = get_fiberpos_data(pos, coord_df, fiberpos)
        pos_telem = add_posmove_telemetry(ptl, dev, start, end, exp_df_base, ptl_dbs)
        final_pos_df = pd.merge(pos_df, pos_telem, on=['EXPID'], how='left')
        final_pos_df = pd.merge(final_pos_df, telem_df, on=['EXPID'], how='left')
        save_data(pos, final_pos_df, mode)
        print('Pos {} Done: {}'.format(pos, datetime.now()))
    except Exception as e:
        print("Issue with {}: {}".format(pos,e))



