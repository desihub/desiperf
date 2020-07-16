
import pandas as pd
import fnmatch
import numpy as np
import os, glob

from astropy.table import Table
from astropy.time import Time
import psycopg2
from datetime import datetime
from bokeh.models import ColumnDataSource


class DataSource():
    # Currently this only works on the DESI Server
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

        self.qa_dir = '/exposures/nightwatch/'
        self.coord_dir = '/exposures/desi/'

        self.exp_df = None

    def db_query(self, table_name, sample = None, table_type = 'telemetry'):
        """
        sample: int number of data points to take. If sample=60, it will sample every 60th data point.
        """
        self.conn = psycopg2.connect(host="desi-db", port="5442", database="desi_dev",
                  user="desi_reader", password="reader")
        if table_type == 'telemetry':
            query = pd.read_sql_query(f"SELECT * FROM {table_name} WHERE time_recorded >= '{self.start_date}' AND time_recorded <'{self.end_date}'",self.conn)
        elif table_type == 'exposure':
            #start, end = self.get_mjd_times([self.start_date, self.end_date], time_type='date')
            query = pd.read_sql_query(f"SELECT * FROM {table_name} WHERE date_obs >= '{self.start_date}' AND date_obs < '{self.end_date}'",self.conn)
        
        # Resample data. Most telemetry streams are taken every 1.5 seconds. 
        if isinstance(sample, int): 
            query = query[query.index % sample == 0]
        return query

    def get_exp_df(self):
        self.exp_df = self.db_query('exposure',table_type='exposure')
        self.full_exp_list = self.exp_df[['id','date_obs']].to_records()

    def align_datasets(self, df_with_exp, df_with_time):
        for col in ['EXPOSURE','EXPID']:
            if col in df_with_exp.columns:
                exposures = [int(exp) for exp in np.unique(df_with_exp[col])]

        df_with_time = self.telemetry_for_exposures(exposures, df_with_time)
        df_with_exp.reset_index(inplace=True, drop=True)
        df_with_time.reset_index(inplace=True,drop=True)
        combined_df = pd.concat([df_with_exp, df_with_time], axis=1)
        return combined_df

    def convert_time_to_exp(self, exposures, tele_df):
        
        if self.exp_df is None:
            self.get_exp_df()

        #Convert times to MJD
        times = self.get_mjd_times(tele_df.time_recorded)

        #Get times of exposures
        idx = []
        for t in self.exp_df[self.exp_df.id.isin(exposures)].mjd_obs:
            dt = [np.abs(tt-t) for tt in times]
            idx.append(np.argmin(dt))

        #Select data from time data that corresponds with exposures
        new_df = tele_df.iloc[idx]

        #give exposure number to time data
        new_df['EXPID'] = list(self.exp_df[self.exp_df.id.isin(exposures)].id)
        return new_df

    def get_qa_data(self, hdu_name, cols):

        if self.exp_df is None:
            self.get_exp_df()

        qa_files = []
        #for row in exposure_array:
        #    date = np.datetime_as_string(row['date_obs'],unit='D').replace('-','') #prob need to manipulate
        #    exp = str(int(row['id'])).zfill(8)
        for date in np.unique(self.full_exp_list['date_obs']):
            date = np.datetime_as_string(date, unit='D').replace('-','')
            qa_files.append(glob.glob(self.qa_dir+'{}/*/qa-*.fits'.format(date)))
        qa_files = np.hstack(qa_files)
        D = []
        for qa in qa_files:
            try:
                hdu = fits.open(qa)
                try:
                    df = Table(hdu[hdu_name]).to_pandas()#'PER_AMP'
                    D.append(df[cols]) #
                except:
                    pass
            except:
                print(qa)

        df = pd.DataFrame(np.vstack(D), columns = cols)
        return df

    def get_coord_files(self):
        if self.exp_df is None:
            self.get_exp_df()
        
        exp_list = self.exp_df[self.exp_df.sequence == 'DESI']
        self.coord_files = []
        for date in np.unique(exp_list['date_obs']):
            date = np.datetime_as_string(date, unit='D').replace('-','')
            files = glob.glob(self.coord_dir+'{}/*/coordinates-*'.format(date))
            for f in files:
                try:
                    df = Table.read(f, format='fits').to_pandas()
                    good = df['OFFSET_0']
                    self.coord_files.append(f)
                except:
                    pass

    def fp_pos_accuracy(self):
        def rms(x):
            return np.sqrt(np.mean(np.array(x)**2))
        print('here')    
        self.get_coord_files()
        print(len(self.coord_files))
        data = []
        for f in self.coord_files:
            exp_id = int(f[-13:-5])

            df = Table.read(f,format='fits').to_pandas()
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
                    print(f)
            except:
                print('failed blind',f)

        df = pd.DataFrame(np.vstack(data), columns=['EXPOSURE','max_blind','max_blind_95','rms_blind',
                                                        'rms_blind_95', 'max_corr', 'max_corr_95', 
                                                        'rms_corr', 'rms_corr_95'])
        return df


    def get_mjd_times(self, time_list, time_type = 'Timestamp'):
        if time_type == 'Timestamp':
            times = [Time(t).mjd for t in time_list]
        elif time_type == 'date':
            times = [Time(datetime.strptime(t, '%Y%m%d')).mjd for t in time_list]

        return times
        
