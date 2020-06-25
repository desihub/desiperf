import pandas as pd
import numpy as np
import os, glob
import fnmatch
import matplotlib.pyplot as plt
from astropy.table import Table
import psycopg2
from datetime import datetime
from bokeh.models import ColumnDataSource


class DataHandler(object):
    def __init__(self, start_date = '2020-01-23', end_date = '2020-03-16'):
        self.start_date = start_date
        self.end_date = end_date
        self.data_columns = [ 'skyra', 'skydec',  'exptime',
                            'tileid',  'airmass', 'mountha', 'zd', 'mountaz',
                            'domeaz', 
                            'zenith', 'mjd_obs',  'moonra',
                            'moondec',   'EXPOSURE', 'max_blind',
                            'max_blind_95', 'rms_blind', 'rms_blind_95', 'max_corr',
                            'max_corr_95', 'rms_corr', 'rms_corr_95', 'mirror_temp',
                            'truss_temp', 'air_temp', 'mirror_avg_temp', 'wind_speed',
                            'wind_direction', 'humidity', 'pressure', 'temperature',
                            'dewpoint', 'shutter_open', 'exptime_sec', 'psf_pixels'] #'hexapod', 'adc','spectrographs',
                            #'image_cameras', 'guide_cameras', 'focus_cameras','date_obs','time_between_exposures',  'excluded',
                            #'s2n', 'transpar', 'skylevel','st', 'hexapod_time', 'slew_time','moonangl',
                            #'aos', 'seeing', 'guider', 'focus','utc_dark', 'utc_beg',
                            #'utc_end', 'reqra', 'reqdec','deltara', 'deltadec',
                            #'targtra','targtdec', 'telstat',
        try:
            self.conn = psycopg2.connect(host="desi-db", port="5442", database="desi_dev",
                        user="desi_reader", password="reader")
        except:
            pass
        try:
            init_data = Table.read('./instperfapp/data/data.fits', format='fits').to_pandas() 
            init_data = init_data[self.data_columns]
            self.data_source = ColumnDataSource(init_data)
        except:
            self.data_source = None

    def get_coord_files(self):
        ## Make this so that it only gets recent data
        all_coord_files = glob.glob('/exposures/desi/*/*/coordinates-*')

        self.coord_files = []
        for f in all_coord_files:
            try:
                df = Table.read(f, format='fits').to_pandas()
                good = df['OFFSET_0']
                if fnmatch.fnmatch(f,'/exposures/desi/202005*/*/*.fits'):
                    pass
                else:
                    self.coord_files.append(f)
            except:
                pass

    def posacc_data(self):

        def rms(x):
            return np.sqrt(np.mean(np.array(x)**2))

        data = []
        for file in self.coord_files:
            exp_id = int(file[-13:-5])

            df = Table.read(file,format='fits').to_pandas()
            good_df = df[df['FLAGS_FVC_0'] == 4]
            blind = np.array(good_df['OFFSET_0'])
            blind = blind[~np.isnan(blind)]
            try:
                max_blind = np.max(blind)*1000
                max_blind_95 = np.max(np.percentile(blind,95))*1000
                rms_blind = rms(blind)*1000
                rms_blind_95 = rms(np.percentile(blind,95))*1000

                cols = df.columns
                try:
                    final_move = np.sort(fnmatch.filter(cols, 'OFFSET_*'))[-1][-1]
                    good_df = df[df['FLAGS_FVC_%s'%final_move] == 4]
                    final = np.array(list(good_df['OFFSET_%s'%final_move]))
                    final = final[~np.isnan(final)]
                    max_corr = np.max(final)*1000
                    max_corr_95 = np.max(np.percentile(final,95))*1000
                    rms_corr = rms(final)*1000
                    rms_corr_95 = rms(np.percentile(final,95))*1000
                    data.append([exp_id, max_blind, max_blind_95, rms_blind, rms_blind_95, 
                                 max_corr, max_corr_95, rms_corr, rms_corr_95])  
                except:
                    print(file)
            except:
                print('failed blind',file)
        self.exp_df = pd.DataFrame(np.vstack(data), columns=['EXPOSURE','max_blind','max_blind_95','rms_blind',
                                                        'rms_blind_95', 'max_corr', 'max_corr_95', 
                                                        'rms_corr', 'rms_corr_95'])
        self.exposures = [int(e) for e in self.exp_df.EXPOSURE]

    def get_temp_values(self,query, dtimes, times, cols):
        results = []
        for t in times:
            idx = np.abs([d-t for d in dtimes]).argmin()
            data = query.iloc[idx]
            ret = []
            for col in cols:
                ret.append(data[col])
            results.append(ret)
        df = pd.DataFrame(np.vstack(results), columns = cols)
        return df

    def telemetry_queries(self):
        exp_query = pd.read_sql_query(f"SELECT * FROM exposure WHERE time_recorded >= '{self.start_date}' AND time_recorded <'{self.end_date}'",self.conn)
        new_query = exp_query[exp_query.id.isin(self.exposures)]
        new_df = pd.merge(left=new_query, right=self.exp_df, left_on='id', right_on='EXPOSURE')
        times = list(new_df.mjd_obs)

        tempquery = pd.read_sql_query(f"SELECT * FROM environmentmonitor_telescope WHERE time_recorded >= '{self.start_date}' AND time_recorded < '{self.end_date}'",self.conn)
        towerquery = pd.read_sql_query(f"SELECT * FROM environmentmonitor_tower WHERE time_recorded >= '{self.start_date}' AND time_recorded < '{self.end_date}'",self.conn)

        temp_cols = ['mirror_temp','truss_temp','air_temp','mirror_avg_temp']
        tower_cols = ['wind_speed','wind_direction', 'humidity', 'pressure', 'temperature', 'dewpoint']

        temp_dtimes = [Time(datetime.strptime(t,'%Y-%m-%d %H:%M:%S')).mjd for t in list(tempquery.telescope_timestamp)]
        tower_dtimes = [Time(datetime.strptime(t,'%Y-%m-%d %H:%M:%S')).mjd for t in list(towerquery.tower_timestamp)]

        temp_df = self.get_temp_values(tempquery, temp_dtimes, times, temp_cols)
        tower_df = self.get_temp_values(towerquery, tower_dtimes, times, tower_cols)

        ## FVC Data
        fvcquery = pd.read_sql_query(f"SELECT * FROM fvc_camerastatus WHERE time_recorded >= '{self.start_date}' AND time_recorded <'{self.end_date}'",self.conn)
        fvc_cols = ['shutter_open','exptime_sec','psf_pixels']
        fvc_dtimes = [Time(t.to_datetime64()).mjd for t in list(fvcquery.time_recorded)]
        fvc_df = self.get_temp_values(fvcquery, fvc_dtimes, times, fvc_cols)

        ## Combine them all!
        self.results = pd.concat([new_df,temp_df,tower_df,fvc_df],axis=1)

    def update_data(self):
        print('here1')
        self.get_coord_files()
        print('here2')
        self.posacc_data()
        print('here3')
        self.telemetry_queries()
        print('here4')

        table = Table.from_pandas(self.results)
        table.write('data.fits',format='fits')

        self.data_source = ColumnDataSource(self.results)
