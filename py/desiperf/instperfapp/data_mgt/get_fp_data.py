import os, glob
import fnmatch
import pandas as pd
import numpy as np
from astropy.io import fits
import psycopg2
from astropy.table import Table

from datetime import datetime

start = datetime.now()

class FPData():
    def __init__(self, start, end):
        self.start_date = start
        self.end_date = end

        self.conn = psycopg2.connect(host="desi-db", port="5442", database="desi_dev", user="desi_reader", password="reader")

    def get_exp_df(self):
        exp_cols = ['id','data_location','targtra','targtdec','skyra','skydec','deltara','deltadec','reqtime','exptime','flavor','program','lead','focus','airmass',
            'mountha','zd','mountaz','domeaz','spectrographs','s2n','transpar','skylevel','zenith','mjd_obs','date_obs','night','moonra','moondec','parallactic','mountel',
            'dome','telescope','tower','hexapod','adc','sequence','obstype']

        exp_df = pd.read_sql_query(f"SELECT * FROM exposure WHERE date_obs >= '{self.start_date}' AND date_obs < '{self.end_date}'", self.conn)

        exp_df_new = exp_df[exp_cols]
        self.exp_df_new = exp_df_new.rename(columns={'id':'EXPID'})

        self.exp_df_base = self.exp_df_new[['EXPID','date_obs']]

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

        gfa_df = pd.concat(dfs, axis=1)
        gfa_df.to_csv('gfa_by_unit.csv')

        gfa_mean_df = self.exp_df_base.copy()
        for attr in gfa_cols[1:-1]: 
            x = []
            for i in range(10):
                df = dfs[i]
                x.append(df[attr+'_{}'.format(i)])
            gfa_mean_df[attr+'_mean'] = np.mean(x, axis=0)
   
        self.gfa_df_final = self.remove_repeats(gfa_mean_df)

    def get_guider_df(self):
        gs_cols = ['duration','expid','seeing','frames','meanx','meany','meanx2','meany2','meanxy','maxx','maxy']
        gc_cols = ['combined_x','combined_y','time_recorded']

        gs_df = pd.read_sql_query(f"SELECT * FROM guider_summary WHERE time_recorded >= '{self.start_date}' AND time_recorded <'{self.end_date}'", self.conn)
        gc_df = pd.read_sql_query(f"SELECT * FROM guider_centroids WHERE time_recorded >= '{self.start_date}' AND time_recorded <'{self.end_date}'", self.conn)

        #Guider Summary
        gs_df = gs_df[gs_cols]
        gs_df = gs_df[np.isfinite(gs_df.expid)]

        gs_df_final = pd.merge(self.exp_df_base, gs_df, left_on='EXPID', right_on='expid', how='left')
        gs_df_final.drop_duplicates(subset=['EXPID'], keep='first', inplace=True)
        self.gs_df_final = self.remove_repeats(gs_df_final)

        #Guider Centroids
        gc_df = gc_df[gc_cols]
        idx = []
        for time in self.exp_df_base.date_obs:
            ix = np.argmin(np.abs(gc_df['time_recorded'] - time))
            idx.append(ix)
        gc_df_new = gc_df.iloc[idx]
        gc_df_new = gc_df_new.rename(columns={'time_recorded':'guider_time_recorded'})
        self.gc_df_final = gc_df_new.reset_index(drop=True)

    def get_fvc_df(self):
        fvc_cols = ['shutter_open','fan_on','temp_degc','exptime_sec','psf_pixels','time_recorded']

        fvc_df = pd.read_sql_query(f"SELECT * FROM fvc_camerastatus WHERE time_recorded >= '{self.start_date}' AND time_recorded <'{self.end_date}'", self.conn)
        
        fvc_df = fvc_df[fvc_cols]
        idx = []
        for time in self.exp_df_base.date_obs:
            ix = np.argmin(np.abs(fvc_df['time_recorded'] - time))
            idx.append(ix)
        fvc_df_new = fvc_df.iloc[idx]
        fvc_df_new = fvc_df_new.rename(columns={'time_recorded':'fvc_time_recorded'})
        self.fvc_df_final = fvc_df_new.reset_index(drop=True)

    def get_hex_df(self):
        hex_cols = ['rot_rate', 'hex_status', 'rot_offset', 'rot_enabled', 'rot_interval', 'hex_trim_0', 'hex_position_0',
            'hex_trim_1', 'hex_position_1', 'hex_trim_2', 'hex_position_2','hex_trim_3', 'hex_position_3', 'hex_trim_4', 
            'hex_position_4','hex_trim_5', 'hex_position_5','hex_tweak']

        dd = {key: [] for key in hex_cols}

        for item in self.exp_df_new['hexapod']:
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

        self.hex_df = pd.DataFrame.from_dict(dd)

    def get_adc_df(self):
        adc_cols = ['adc_home1', 'adc_home2', 'adc_nrev1', 'adc_nrev2', 'adc_angle1','adc_angle2']
        dd = {key: [] for key in adc_cols}

        for item in self.exp_df_new['adc']:
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

        self.adc_df = pd.DataFrame.from_dict(dd)

    def get_telem_df(self):
        dfs = []
        for d in ['telescope','tower','dome']:
            try:
                t_keys = list(self.exp_df_new.iloc[0][d].keys())
            except:
                t_keys = list(self.exp_df_new.iloc[1][d].keys())
            dd = {}
            for t in t_keys:
                dd[t] = []
            for item in self.exp_df_new[d]:
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
        self.telem_df = pd.concat(dfs, axis=1)

    def remove_bad_attr(self, df):
        no_longer_needed = ['telescope','tower','dome','hexapod','adc']
        df.drop(no_longer_needed, axis=1, inplace=True)

        bad_attr = ['chimney_ib_temp','chimney_im_temp','chimney_it_temp','chimney_os_temp','chimney_ow_temp','probe1_temp','probe2_temp',
        'probe1_humidity','probe2_humidity','lights_high','lights_low','mirror_status','mirror_covers','shutter_uppper','shutter_low']
        df.drop(bad_attr, axis=1, inplace=True, errors='ignore')
        return df

    def remove_repeats(self, df):
        df.drop(['EXPID','date_obs'], axis=1, inplace=True)
        return df

    def rms(self, x):
        return np.sqrt(np.mean(np.array(x)**2))

    def get_coord_files(self):
        nights = np.unique(self.exp_df_new['night'])
        dates = [int(d) for d in nights[np.isfinite(nights)]]

        start = datetime.now()
        coord_dir = '/exposures/desi/'
        self.all_coord_files = {}
        for date in dates:
            self.all_coord_files[date] = []
            coord_files = glob.glob(coord_dir+'{}/*/coordinates-*'.format(date))
            for f in coord_files:
                try:
                    df = Table.read(f, format='fits').to_pandas()
                    good = df['OFFSET_0']
                    self.all_coord_files[date].append(f)
                except:
                    pass

    def get_pos_acc(self, f):
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
            rms_blind = self.rms(blind)*1000
            rms_blind_95 = self.rms(np.percentile(blind,95))*1000
            cols = df.columns
            final_move = np.sort(fnmatch.filter(cols, 'OFFSET_*'))[-1][-1]
            final = np.array(list(good_df['OFFSET_%s'%final_move]))
            final = final[~np.isnan(final)]
            max_corr = np.max(final)*1000
            max_corr_95 =  np.max(np.percentile(final,95))*1000
            rms_corr = self.rms(final)*1000
            rms_corr_95 = self.rms(np.percentile(final,95))*1000
            data = [exp,  max_blind, max_blind_95, rms_blind, rms_blind_95, max_corr, max_corr_95, rms_corr, rms_corr_95]
                                                                                                                                                          
            return data 
        except:
            print('failed:',f)
            return None

    def get_pos_df(self):
        self.get_coord_files()
        all_data = []
        for date, files in self.all_coord_files.items():
            for f in files:
                data = self.get_pos_acc(f)
                if data is not None:
                    all_data.append(data)

        pos_df = pd.DataFrame(np.vstack(all_data), columns =
            ['EXPID','MAX_BLIND','MAX_BLIND_95','RMS_BLIND','RMS_BLIND_95','MAX_CORR','MAX_CORR_95','RMS_CORR','RMS_CORR_95'])
        pos_df_final = pd.merge(self.exp_df_base, pos_df, on='EXPID',how='left')
        self.pos_df_final = self.remove_repeats(pos_df_final)

    def run(self):
        start = datetime.now()
        print('Start: {}'.format(start))
        self.get_exp_df()
        print('Exp: {}'.format(datetime.now()))
        self.get_guider_df()
        print('Guider: {}'.format(datetime.now()))
        self.get_fvc_df()
        print('FVC: {}'.format(datetime.now()))
        self.get_gfa_df()
        print('GFA: {}'.format(datetime.now()))
        self.get_hex_df()
        print('Hex: {}'.format(datetime.now()))
        self.get_adc_df()
        print('ADC: {}'.format(datetime.now()))
        self.get_telem_df()
        print('Telemetry: {}'.format(datetime.now()))

        self.get_pos_df()
        print('POS: {}'.format(datetime.now()))
        
        all_dfs = [self.exp_df_new, self.gfa_df_final, self.gc_df_final, self.gs_df_final, self.telem_df, self.hex_df, self.adc_df, self.fvc_df_final, self.pos_df_final]
        for i, df in enumerate(all_dfs):
            df.reset_index(drop=True, inplace=True)
            print(df.shape)
            all_dfs[i] = df

        final_df = pd.concat(all_dfs, axis=1)
        print(final_df.shape)
        final_df = self.remove_bad_attr(final_df)
        print(final_df.shape)

        save_dir = './data/focalplane/'
        final_df.to_csv(os.path.join(save_dir,'fpa_all.csv'),index=False)
        df = pd.read_csv(os.path.join(save_dir,'fpa_all.csv'))
        t = Table.from_pandas(df)
        for col in t.columns: 
            if t[col].dtype == 'object': 
                t[col] = np.array(t[col].astype('str'))
        print(t.dtype)
        t.write(os.path.join(save_dir,'fpa_all.fits.gz'), format='fits')


        # dfs = np.array_split(final_df, 10)
        # for i, df in enumerate(dfs):
        #     df.to_csv(save_dir+'fpa_data_{}.csv'.format(i),index=False)
        print("FP Done")



