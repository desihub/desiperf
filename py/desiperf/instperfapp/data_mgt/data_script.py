import os, glob
import fnmatch
import pandas as pd
import numpy as np
from astropy.io import fits
import psycopg2
from astropy.table import Table

from datetime import datetime

start = datetime.now()

start_date = '20200121'
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

gfa_df = pd.concat(new_dfs, axis=1)
gfa_df.to_csv('gfa_by_unit.csv')

gfa_mean_df = exp_df_base.copy()
for attr in ['ccdtemp','hotpeltier','coldpeltier','filter','humid2','humid3','fpga','camerahumid','cameratemp']:
    x = []
    for i in range(10):
        df = new_dfs[i]
        x.append(df[attr+'_{}'.format(i)])
    gfa_mean_df[attr+'_mean'] = np.mean(x, axis=0)

del gfa_mean_df['EXPID']
del gfa_mean_df['date_obs']

gfa_df_final = gfa_mean_df #pd.concat(all_dfs, axis=1)

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

spec_df = pd.read_sql_query(f"SELECT * FROM spectrographs_sensors WHERE time_recorded >= '{start_date}' AND time_recorded <'{end_date}'", conn)
spec_df_new = spec_df[spec_cols]

dfs = []
for un in range(10):
    df = spec_df_new[spec_df_new.unit == un]
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
    #new_cols = df.columns[1:-1]
    #df = df[new_cols]
    new_dfs.append(df)

for i, df in enumerate(new_dfs):
    df = df.reset_index(drop=True)
    new_dfs[i] = df

spec_df = pd.concat(new_dfs, axis=1)
spec_df.to_csv('spec_by_unit.csv')

spec_mean_df = exp_df_base.copy()
for attr in ['nir_camera_temp', 'nir_camera_humidity','red_camera_temp', 'red_camera_humidity', 'blue_camera_temp','blue_camera_humidity', 'bench_cryo_temp', 'bench_nir_temp','bench_coll_temp', 'ieb_temp']:
    x = []
    for i in range(10):
        df = new_dfs[i]
        x.append(df[attr+'_{}'.format(i)])
    spec_mean_df[attr+'_mean'] = np.mean(x, axis=0)

del spec_mean_df['EXPID']
del spec_mean_df['date_obs']

spec_df_final =  spec_mean_df


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

all_dfs = {'exp_df':exp_df_new, 'gfa_df':gfa_df_final, 'gc_df':gc_df_final, 'gs_df':gs_df_final, 'telem_df':telem_df, 'hex_df':hex_df, 'adc_df':adc_df, 'fvc_df':fvc_df_final, 'spec_df_final': spec_df_final}
for name, df in all_dfs.items():
    df.reset_index(drop=True, inplace=True)
    print(name)
    print(np.array(df.columns))
    print('------------')
    all_dfs[name] = df

final_df = pd.concat(list(all_dfs.values()), axis=1)

# REMOVE USELESS ATTR
bad_attr = ['chimney_ib_temp','chimney_im_temp','chimney_it_temp','chimney_os_temp','chimney_ow_temp','probe1_temp','probe2_temp','probe1_humidity','probe2_humidity','lights_high','lights_low','mirror_status','mirror_covers','shutter_uppper','shutter_low']
final_df.drop(bad_attr, axis=1, inplace=True)


final_df.to_csv('fp_telemetry.csv',index=False)
print(datetime.now() - start)

###COORDINATE FILES

nights = np.unique(exp_df['night'])
dates = [int(d) for d in nights[np.isfinite(nights)]]

start = datetime.now()
coord_dir = '/exposures/desi/'
all_coord_files = {}
for date in dates:
    all_coord_files[date] = []
    coord_files = glob.glob(coord_dir+'{}/*/coordinates-*'.format(date))
    for f in coord_files:
        try:
            df = Table.read(f, format='fits').to_pandas()
            good = df['OFFSET_0']
            all_coord_files[date].append(f)
        except:
            pass

def rms(x):
    return np.sqrt(np.mean(np.array(x)**2))

def get_pos_acc(f):
    date, exp = os.path.split(f)[0].split('/')[-2:]
    date = int(date)
    exp = int(exp)

    df = Table.read(f,format='fits').to_pandas()
    good_df = df[df['FLAGS_FVC_0'] == 4]

    try:
        blind = np.array(good_df['OFFSET_0'])
        blind = blind[~np.isnan(blind)]
        max_blind = np.max(blind)*1000
        max_blind_95 = np.max(np.percentile(blind,95))*1000
        rms_blind = rms(blind)*1000
        rms_blind_95 = rms(np.percentile(blind,95))*1000
        cols = df.columns
        final_move = np.sort(fnmatch.filter(cols, 'OFFSET_*'))[-1][-1]
        final = np.array(list(good_df['OFFSET_%s'%final_move]))
        final = final[~np.isnan(final)]
        max_corr = np.max(final)*1000
        max_corr_95 =  np.max(np.percentile(final,95))*1000
        rms_corr = rms(final)*1000
        rms_corr_95 = rms(np.percentile(final,95))*1000
        data = [exp,  max_blind, max_blind_95, rms_blind, rms_blind_95, max_corr, max_corr_95, rms_corr, rms_corr_95]
                                                                                                                                                      
        return data 
    except:
        print('failed:',f)
        return None
all_data = []
for date, files in all_coord_files.items():
    for f in files:
        data = get_pos_acc(f)
        if data is not None:
            all_data.append(data)

pos_df = pd.DataFrame(np.vstack(all_data), columns =
['EXPID','MAX_BLIND','MAX_BLIND_95','RMS_BLIND','RMS_BLIND_95','MAX_CORR','MAX_CORR_95','RMS_CORR','RMS_CORR_95'])
full_df = pd.merge(exp_df, pos_df, on='EXPID',how='left')
full_df.to_csv('fp_data.csv',index=False)
print(datetime.now() - start)

####QA FILES

gfa_df = pd.read_csv('gfa_by_unit.csv')
gfa_cols = ['ccdtemp','hotpeltier','coldpeltier','filter','humid2','humid3','fpga','camerahumid','cameratemp']
spec_df = pd.read_csv('spec_by_unit.csv')
spec_cols = ['nir_camera_temp', 'nir_camera_humidity','red_camera_temp', 'red_camera_humidity', 'blue_camera_temp','blue_camera_humidity',
'bench_cryo_temp', 'bench_nir_temp','bench_coll_temp', 'ieb_temp']

def combine_specs(df_, cols_):
    dfs = []
    for un in range(10):
        cols = []
        for attr in cols_:
            cols.append(attr+'_{}'.format(un))
        df = df_[cols]
        df['SPECTRO'] = un
        new_cols = {}
        for col in cols_:
            new_cols[col+'_{}'.format(un)] = col
        df = df.rename(columns=new_cols)
        dfs.append(df)
    for i, df in enumerate(dfs):
        new_df = pd.concat([exp_df_base, df], axis = 1)
        dfs[i] = new_df
    df_final  = pd.concat(dfs)
    return df_final

gfa_df_final = combine_specs(gfa_df, gfa_cols)
spec_df_final = combine_specs(spec_df, spec_cols)

others_df = pd.merge(gfa_df_final, spec_df_final, on=['EXPID','SPECTRO'], how='inner')
print(gfa_df_final.shape)
print(spec_df_final.shape)
print(others_df.shape)

all_qa_files = {}
for date in dates:
    files = glob.glob('/exposures/nightwatch/{}/*/qa-*.fits'.format(date))
    all_qa_files[date] = files

per_amp_cols = ['NIGHT', 'EXPID', 'SPECTRO','CAM', 'AMP', 'READNOISE','BIAS', 'COSMICS_RATE']

def get_qa_data(f):
    hdulist = fits.open(f)
    hdu_names = [hdulist[i].name for i in range(len(hdulist))]
    if 'PER_AMP' in hdu_names:
        per_amp_df = Table(hdulist['PER_AMP'].data).to_pandas()
        final_df = per_amp_df[per_amp_cols]
    if 'PER_CAMERA' in hdu_names:
        per_cam_df = Table(hdulist['PER_CAMERA'].data).to_pandas()
        final_df = pd.merge(final_df, per_cam_df, on=['NIGHT','EXPID','SPECTRO','CAM'],how='left')
    if 'PER_CAMFIBER' in hdu_names:
        df = Table(hdulist['PER_CAMFIBER'].data).to_pandas()
        mean_values = []
        for cam in np.unique(df.CAM):
            ddf = df[df.CAM == cam]
            for spec in np.unique(df.SPECTRO):
                dd = ddf[ddf.SPECTRO == spec]
                vals = [cam, spec]
                for attr in ['INTEG_RAW_FLUX','MEDIAN_RAW_FLUX', 'MEDIAN_RAW_SNR']:
                    x = np.mean(dd[attr])
                    vals.append(x)
                mean_values.append(vals)
        per_camf_df = pd.DataFrame(np.vstack(mean_values), columns = ['CAM','SPECTRO','INTEG_RAW_FLUX','MEDIAN_RAW_FLUX', 'MEDIAN_RAW_SNR'])
        per_camf_df['SPECTRO'] = per_camf_df['SPECTRO'].astype('int64')
        final_df = pd.merge(final_df, per_camf_df, on = ['SPECTRO','CAM'], how='left')

    if 'PER_FIBER' in hdu_names:
        df = Table(hdulist['PER_FIBER'].data).to_pandas()
        mean_values  =[]
        for cam in ['B','R','Z']:
            for spec in np.unique(df.SPECTRO):
                ddf = df[df.SPECTRO == spec]
                vals = [cam, spec]
                for attr in ['FLUX_','SNR_','SPECFLUX_','THRU_']:
                    try:
                        x = np.mean(ddf[attr+cam])
                    except:
                        if cam == 'B':
                            try:
                                x = np.mean(ddf[attr+'G'])
                            except:
                                x = np.nan
                    vals.append(x)
                mean_values.append(vals)
        per_fib_df = pd.DataFrame(np.vstack(mean_values), columns = ['CAM','SPECTRO','FLUX','SNR','SPECFLUX','THRU'])
        per_fib_df['SPECTRO'] = per_fib_df['SPECTRO'].astype('int64')
        final_df = pd.merge(final_df, per_fib_df, on=['CAM','SPECTRO'], how='left')
    return final_df


dfs = []
start = datetime.now()
for night, files in all_qa_files.items():
    for f in files:
        dfs.append(get_qa_data(f))

qa_df = pd.concat(dfs)
a = pd.merge(qa_df, others_df, on=['EXPID','SPECTRO'], how='left')
print(qa_df.shape)
print(a.shape)
b = pd.merge(a, exp_df, on='EXPID', how='left')
print(b.shape)
b.to_csv('qa_data.csv',index=False)
print(datetime.now() - start)





