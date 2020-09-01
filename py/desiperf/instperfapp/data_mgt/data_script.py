import pandas as pd
import numpy as np
import psycopg2
import pdb

from datetime import datetime

start = datetime.now()

start_date = '20200120'
end_date = '20200317'

exp_cols = ['id','data_location','targtra','targtdec','skyra','skydec','deltara','deltadec','reqtime','exptime','flavor','program','lead','focus','airmass', 
            'mountha','zd','mountaz','domeaz','spectrographs','s2n','transpar','skylevel','zenith','mjd_obs','date_obs','night','moonra','moondec','parallactic','mountel', 
            'dome','telescope','tower','hexapod','adc','sequence','obstype'] 

conn = psycopg2.connect(host="desi-db", port="5442", database="desi_dev",
                  user="desi_reader", password="reader")

exp_df = pd.read_sql_query(f"SELECT * FROM exposure WHERE date_obs >= '{start_date}' AND date_obs < '{end_date}'",conn)

exp_df_new = exp_df[exp_cols]
exp_df_new = exp_df_new.rename(columns={'id':'EXPID'})
print(exp_df_new.shape)
exp_df_base = exp_df_new[['EXPID','date_obs']] 

#GFA DATA
gfa_cols = ['time_recorded','ccdtemp','hotpeltier','coldpeltier','filter','humid2','humid3','fpga','camerahumid','cameratemp','unit']

gfa_df = pd.read_sql_query(f"SELECT * FROM gfa_telemetry WHERE time_recorded >= '{start_date}' AND time_recorded <'{end_date}'", conn)
gfa_df_new = gfa_df[gfa_cols]

dfs = []
for un in range(10): 
    df = gfa_df_new[gfa_df_new.unit == un] 
    dfs.append(df)  

for i, df in enumerate(dfs): 
    cold = {} 
    for col in df.columns: 
        new_col = col + '_' + str(i) 
        cold[col] = new_col 
    df = df.rename(columns=cold) 
    dfs[i] = df 

new_dfs = []
for i, df in enumerate(dfs): 
    idx = [] 
    for time in exp_df_base.date_obs:  
        ix = np.argmin(np.abs(df['time_recorded_{}'.format(i)] - time))  
        idx.append(ix) 
    df = df.iloc[idx] 
    new_cols = df.columns[1:-1] 
    df = df[new_cols] 
    new_dfs.append(df)

for i, df in enumerate(new_dfs): 
    df = df.reset_index(drop=True)  
    new_dfs[i] = df 

gfa_mean_df = exp_df_base.copy()
for attr in ['ccdtemp','hotpeltier','coldpeltier','filter','humid2','humid3','fpga','camerahumid','cameratemp']: 
    x = [] 
    for i in range(10): 
        df = new_dfs[i] 
        x.append(df[attr+'_{}'.format(i)]) 
    gfa_mean_df[attr+'_mean'] = np.mean(x, axis=0) 

all_dfs = [gfa_mean_df]
for df in new_dfs:
    all_dfs.append(df)

gfa_df_final = pd.concat(all_dfs, axis=1)
del gfa_df_final['EXPID']
del gfa_df_final['date_obs']
#GUIDER SUMMARY
gs_df = pd.read_sql_query(f"SELECT * FROM guider_summary WHERE time_recorded >= '{start_date}' AND time_recorded <'{end_date}'", conn)

gs_cols = ['duration','expid','seeing','frames','meanx','meany','meanx2','meany2','meanxy','maxx','maxy']
gs_df = gs_df[gs_cols]
gs_df = gs_df[np.isfinite(gs_df.expid)]

gs_df_final = pd.merge(exp_df_base, gs_df, left_on='EXPID', right_on='expid', how='left')
gs_df_final.drop_duplicates(subset=['EXPID'], keep='first', inplace=True)
del gs_df_final['EXPID']
del gs_df_final['date_obs']
#GUIDER CENTROIDS
gc_df = pd.read_sql_query(f"SELECT * FROM guider_centroids WHERE time_recorded >= '{start_date}' AND time_recorded <'{end_date}'", conn)
gc_cols = ['combined_x','combined_y','time_recorded']
gc_df = gc_df[gc_cols]
idx = []
for time in exp_df_base.date_obs: 
    ix = np.argmin(np.abs(gc_df['time_recorded'] - time)) 
    idx.append(ix) 
gc_df_new = gc_df.iloc[idx]
gc_df_new = gc_df_new.rename(columns={'time_recorded':'guider_time_recorded'})
gc_df_final = gc_df_new.reset_index(drop=True)
#gc_df_final = pd.concat([exp_df_base, gc_df_new], axis=1) 

#EXTRACT DICS

dfs = []
for d in ['telescope','tower','dome']: 
    t_keys = list(exp_df_new.iloc[0][d].keys()) 
    dd = {} 
    for t in t_keys: 
        dd[t] = [] 
    for item in exp_df_new[d]: 
        if item is not None: 
            for key, val in item.items(): 
                dd[key].append(val) 
        else: 
            for key, l in dd.items(): 
                dd[key].append(None) 
    df = pd.DataFrame.from_dict(dd) 
    dfs.append(df) 

for i, df in enumerate(dfs): 
    df.reset_index(inplace=True, drop=True) 
    dfs[i] = df
telem_df = pd.concat(dfs, axis=1)

adc_cols = ['adc_home1', 'adc_home2', 'adc_nrev1', 'adc_nrev2', 'adc_angle1','adc_angle2']
dd = {}
for t in adc_cols: 
    dd[t] = [] 
for item in exp_df_new['adc']: 
        if item is not None: 
            for col in adc_cols: 
                try: 
                    val = item[col] 
                except: 
                    val = None 
                dd[col].append(val) 
        else: 
            for col in adc_cols: 
                dd[col].append(None)

adc_df = pd.DataFrame.from_dict(dd) 

hex_cols = ['rot_rate', 'hex_status', 'rot_offset', 'rot_enabled',
       'rot_interval', 'hex_trim_0', 'hex_position_0',
       'hex_trim_1', 'hex_position_1', 'hex_trim_2', 'hex_position_2',
       'hex_trim_3', 'hex_position_3', 'hex_trim_4', 'hex_position_4',
       'hex_trim_5', 'hex_position_5','hex_tweak']
dd = {}
for t in hex_cols:
    dd[t] = []

for item in exp_df_new['hexapod']: 
    if item is not None: 
        for key in ['rot_rate','hex_status','rot_offset','rot_enabled','rot_interval','hex_tweak']: 
            try: 
                val = item[key] 
            except: 
                val = None 
            dd[key].append(val) 
        for key in ['hex_trim','hex_position']: 
            try: 
                for i,v in enumerate(item[key]): 
                    dd['{}_{}'.format(key, i)].append(v) 
            except: 
                for i in range(6): 
                    dd['{}_{}'.format(key,i)].append(None) 
    else: 
        for key in hex_cols: 
            dd[key].append(None) 

hex_df = pd.DataFrame.from_dict(dd) 

# SPECT Data
spec_cols = ['nir_camera_temp', 'nir_camera_humidity','red_camera_temp', 'red_camera_humidity', 'blue_camera_temp','blue_camera_humidity', 'bench_cryo_temp', 'bench_nir_temp','bench_coll_temp', 'ieb_temp', 'time_recorded', 'unit']

gfa_df = pd.read_sql_query(f"SELECT * FROM gfa_telemetry WHERE time_recorded >= '{start_date}' AND time_recorded <'{end_date}'", conn)
gfa_df_new = gfa_df[gfa_cols]

dfs = []
for un in range(10):
    df = gfa_df_new[gfa_df_new.unit == un]
    dfs.append(df)

    for i, df in enumerate(dfs):
        cold = {}
        for col in df.columns:
            new_col = col + '_' + str(i)
            cold[col] = new_col
            df = df.rename(columns=cold)
            dfs[i] = df

            new_dfs = []
            for i, df in enumerate(dfs):
                idx = []
                for time in exp_df_base.date_obs:
                    ix = np.argmin(np.abs(df['time_recorded_{}'.format(i)] - time))
                idx.append(ix)
                df = df.iloc[idx]
                new_cols = df.columns[1:-1]
                df = df[new_cols]
                new_dfs.append(df)

            for i, df in enumerate(new_dfs):
                df = df.reset_index(drop=True)
                new_dfs[i] = df

            gfa_mean_df = exp_df_base.copy()
            for attr in ['ccdtemp','hotpeltier','coldpeltier','filter','humid2','humid3','fpga','camerahumid','cameratemp']:
                x = []
                for i in range(10):
                    df = new_dfs[i]
                    x.append(df[attr+'_{}'.format(i)])
                gfa_mean_df[attr+'_mean'] = np.mean(x, axis=0)

             all_dfs = [gfa_mean_df]
            for df in new_dfs:
                 all_dfs.append(df)

            gfa_df_final =  pd.concat(all_dfs, axis=1)


# Shack Data

#FVC Data
fvc_df = pd.read_sql_query(f"SELECT * FROM fvc_camerastatus WHERE time_recorded >= '{start_date}' AND time_recorded <'{end_date}'", conn)
fvc_cols = ['shutter_open','fan_on','temp_degc','exptime_sec','psf_pixels','time_recorded']
fvc_df = fvc_df[fvc_cols]
idx = []
for time in exp_df_base.date_obs: 
    ix = np.argmin(np.abs(fvc_df['time_recorded'] - time)) 
    idx.append(ix)

fvc_df_new = fvc_df.iloc[idx]
fvc_df_new = fvc_df_new.rename(columns={'time_recorded':'fvc_time_recorded'})
fvc_df_final = fvc_df_new.reset_index(drop=True)

#COMBINE ALL

for col in ['telescope','tower','dome','hexapod','adc']:
    del exp_df_new[col]

all_dfs = {'exp_df':exp_df_new, 'gfa_df':gfa_df_final, 'gc_df':gc_df_final, 'gs_df':gs_df_final, 'telem_df':telem_df, 'hex_df':hex_df, 'adc_df':adc_df, 'fvc_df':fvc_df_final}
for name, df in all_dfs.items():
    df.reset_index(drop=True, inplace=True)
    print(name)
    print(df.columns)
    print('------------')
    all_dfs[name] = df

final_df = pd.concat(list(all_dfs.values()), axis=1)
final_df.to_csv('fp_telemetry.csv',index=False)
print(datetime.now() - start)







