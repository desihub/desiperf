import os, glob
import fnmatch
import pandas as pd
import numpy as np
from astropy.io import fits
import psycopg2
from astropy.table import Table

from datetime import datetime

start = datetime.now()

class SPECData():
    def __init__(self, start, end, mode):
        self.mode = mode #new, update
        self.start_date = start
        self.end_date = end

        self.save_dir = self.data_dir = os.path.join(os.environ['DATA_DIR'],'detector')
        self.spec_file = 'spec_all.fits.gz'
        self.conn = psycopg2.connect(host="desi-db", port="5442", database="desi_dev", user="desi_reader", password="reader")

    def get_exp_df(self):
        exp_cols = ['id','data_location','targtra','targtdec','skyra','skydec','deltara','deltadec','reqtime','exptime','flavor','program','lead','focus','airmass',
            'mountha','zd','mountaz','domeaz','spectrographs','s2n','transpar','skylevel','zenith','mjd_obs','date_obs','night','moonra','moondec','parallactic','mountel',
            'dome','telescope','tower','hexapod','adc','sequence','obstype']

        exp_df = pd.read_sql_query(f"SELECT * FROM exposure WHERE date_obs >= '{self.start_date}' AND date_obs < '{self.end_date}'", self.conn)

        exp_df_new = exp_df[exp_cols]
        self.exp_df_new = exp_df_new.rename(columns={'id':'EXPID'})
        self.nights = np.unique(self.exp_df_new['night'])
        self.dates = [int(d) for d in self.nights[np.isfinite(self.nights)]]

        self.exp_df_base = self.exp_df_new[['EXPID','date_obs']]


    def get_spec_df(self):
        spec_cols = ['nir_camera_temp', 'nir_camera_humidity','red_camera_temp', 'red_camera_humidity', 'blue_camera_temp','blue_camera_humidity', 
            'bench_cryo_temp', 'bench_nir_temp','bench_coll_temp', 'ieb_temp', 'time_recorded', 'unit']

        spec_df = pd.read_sql_query(f"SELECT * FROM spectrographs_sensors WHERE time_recorded >= '{self.start_date}' AND time_recorded <'{self.end_date}'", self.conn)
        spec_df_new = spec_df[spec_cols]

        dfs = []
        for un in range(10):
            df = spec_df_new[spec_df_new.unit == un]
            cold = {}
            for col in df.columns:
                new_col = col + '_' + str(un)
                cold[col] = new_col
            df = df.rename(columns=cold)
            idx = []
            for time in self.exp_df_base.date_obs:
                ix = np.argmin(np.abs(df['time_recorded_{}'.format(un)] - time))
                idx.append(ix)
            df = df.iloc[idx]
            df = df.reset_index(drop=True)
            dfs.append(df)

        self.spec_df_final = pd.concat(dfs, axis=1)
        self.spec_df_final['EXPID'] = self.exp_df_base['EXPID']
        #spec_df.to_csv('spec_by_unit.csv')

        spec_mean_df = self.exp_df_base.copy()
        for attr in ['nir_camera_temp', 'nir_camera_humidity','red_camera_temp', 'red_camera_humidity', 'blue_camera_temp','blue_camera_humidity', 'bench_cryo_temp', 'bench_nir_temp','bench_coll_temp', 'ieb_temp']:
            x = []
            for i in range(10):
                df = dfs[i]
                x.append(df[attr+'_{}'.format(i)])
            spec_mean_df[attr+'_mean'] = np.mean(x, axis=0)

        self.spec_mean_df_final = spec_mean_df 

    def get_gfa_df(self):
        gfa_cols = ['time_recorded','ccdtemp','hotpeltier','coldpeltier','filter','humid2','humid3','fpga','camerahumid','cameratemp','unit']

        gfa_df = pd.read_sql_query(f"SELECT * FROM gfa_telemetry WHERE time_recorded >= '{self.start_date}' AND time_recorded <'{self.end_date}'", self.conn)
        gfa_df_new = gfa_df[gfa_cols]

        #Rearrange Columns for GFA by number
        dfs = []
        for un in range(10):
            df = gfa_df_new[gfa_df_new.unit == un]
            cold = {}
            for col in df.columns:
                new_col = col + '_' + str(un)
                cold[col] = new_col
            df = df.rename(columns=cold)
            idx = []
            for time in self.exp_df_base.date_obs:
                ix = np.argmin(np.abs(df['time_recorded_{}'.format(un)] - time))
                idx.append(ix)
            df = df.iloc[idx]
            new_cols = df.columns[1:-1]
            df = df[new_cols]
            df = df.reset_index(drop=True)
            dfs.append(df)

        self.gfa_df_final = pd.concat(dfs, axis=1)
        self.gfa_df_final['EXPID'] = self.exp_df_base['EXPID']

    def get_shack_df(self):
        shack_cols = ['room_pressure','space_temp1', 'reheat_temp', 'space_humidity','time_recorded', 'heater_output', 'space_temp2', 'space_temp4','space_temp_avg', 'space_temp3', 'cooling_coil_temp','chilled_water_output']

        shack_df = pd.read_sql_query(f"SELECT * FROM shack_wec WHERE time_recorded >= '{self.start_date}' AND time_recorded <'{self.end_date}'", self.conn)
        shack_df = shack_df[shack_cols]
        idx = []
        for time in self.exp_df_base.date_obs:
            ix = np.argmin(np.abs(shack_df['time_recorded'] - time))
            idx.append(ix)
        shack_df_new = shack_df.iloc[idx]
        shack_df_new = shack_df_new.rename(columns={'time_recorded':'guider_time_recorded'})
        #shack_df_new['EXPID'] = self.exp_df_base['EXPID'] #pd.concat([shack_df_new, self.exp_df_base])
        self.shack_df_final = shack_df_new.reset_index(drop=True)

    def combine_specs(self, df_, cols_):
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
            df = pd.concat([self.exp_df_base, df], axis = 1)
            dfs.append(df)
        
        df_final  = pd.concat(dfs)
        return df_final

    def per_amp_columns(self, full_df):
        dfs = []
        for amp in ['A','B','C','D']:
            df = full_df[full_df.AMP == amp][['NIGHT','EXPID','SPECTRO','CAM','READNOISE','BIAS', 'COSMICS_RATE']]
            cold = {'NIGHT':'NIGHT','EXPID':'EXPID','SPECTRO':'SPECTRO','CAM':'CAM'}
            for col in ['READNOISE','BIAS', 'COSMICS_RATE']:
                new_col = col + '_' + amp
                cold[col] = new_col
            df = df.rename(columns=cold)
            df = df.reset_index(drop=True)
            dfs.append(df)

        full_df.drop(['AMP','READNOISE','BIAS', 'COSMICS_RATE'], axis=1, inplace=True)
        full_df.drop_duplicates(subset=['NIGHT', 'EXPID', 'SPECTRO','CAM'], keep='first')
        for df in dfs:
            full_df = pd.merge(full_df, df, on=['NIGHT','EXPID','SPECTRO','CAM'], how='left')
        return full_df

    def get_qa_data(self, f):
        per_amp_cols = ['NIGHT', 'EXPID', 'SPECTRO','CAM', 'AMP', 'READNOISE','BIAS', 'COSMICS_RATE']

        hdulist = fits.open(f)
        hdu_names = [hdulist[i].name for i in range(len(hdulist))]
        if 'PER_AMP' in hdu_names:
            per_amp_df = Table(hdulist['PER_AMP'].data).to_pandas()
            final_df = per_amp_df[per_amp_cols]
            final_df = self.per_amp_columns(final_df)

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

    def remove_repeats(self, df):
        df.drop(['EXPID','date_obs'], axis=1, inplace=True)
        return df

    def get_qa_df(self):
        all_qa_files = {date: glob.glob('/exposures/nightwatch/{}/*/qa-*.fits'.format(date)) for date in self.dates}
        
        dfs = []
        for night, files in all_qa_files.items():
            for f in files:
                dfs.append(self.get_qa_data(f))

        self.qa_df = pd.concat(dfs)

    def save_data(self):
        df = pd.read_csv(os.path.join(self.save_dir, 'spec_all.csv'))
        filen = os.path.join(self.save_dir, self.spec_file)
        if self.mode == 'update':
            old_df = Table.read(filen).to_pandas()
            final_df = pd.concat([old_df, df])
            final_df.drop_duplicates(subset=['date_obs'], keep='first', inplace=True)
        elif self.mode == 'new':
            final_df = df

        t = Table.from_pandas(final_df)
        for col in t.columns:
            if t[col].dtype == 'object':
                t[col] = np.array(t[col].astype('str'))
        t.write(filen, format='fits', overwrite=True)

    def run(self):
        print('Start: {}'.format(datetime.now()))
        self.get_exp_df()
        print('Exp: {}'.format(datetime.now()))
        self.get_shack_df()
        print('Shack {}'.format(datetime.now()))
        self.get_spec_df()
        print('Spec telem {}'.format(datetime.now()))
        spec_cols = ['nir_camera_temp', 'nir_camera_humidity','red_camera_temp', 'red_camera_humidity', 'blue_camera_temp','blue_camera_humidity',
        'bench_cryo_temp', 'bench_nir_temp','bench_coll_temp', 'ieb_temp']
        self.spec_df_final = self.combine_specs(self.spec_df_final, spec_cols)

        self.get_gfa_df()
        gfa_cols = ['ccdtemp','hotpeltier','coldpeltier','filter','humid2','humid3','fpga','camerahumid','cameratemp']
        self.gfa_df_final = self.combine_specs(self.gfa_df_final, gfa_cols)

        print('GFA and Spec Final: {}'.format(datetime.now()))
        self.get_qa_df()
        print('QA: {}'.format(datetime.now()))

        all_dfs = [self.exp_df_new, self.gfa_df_final, self.shack_df_final, self.spec_df_final, self.qa_df] 
        for i, df in enumerate(all_dfs):
            df.reset_index(drop=True, inplace=True)
            all_dfs[i] = df
        a = pd.concat([all_dfs[0], all_dfs[2]], axis=1)
        b = pd.merge(all_dfs[1], all_dfs[3],on=['EXPID','SPECTRO'],how='left')
        c = pd.merge(a, b, on='EXPID', how='inner')
        final_df = pd.merge(c, all_dfs[4], on=['EXPID','SPECTRO'],how='left')
        final_df.drop(['zenith'], axis=1, inplace=True)
        print('All merged: {}'.format(datetime.now()))

        #Save as fits.gz
        final_df.to_csv(os.path.join(self.save_dir,'spec_all.csv'),index=False)
        self.save_data()
        print("Spec Done")


