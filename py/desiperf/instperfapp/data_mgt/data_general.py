
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
        self.coord_files = None

        self.fiberpos = pd.read_csv('./instperfapp//data/fiberpos.csv')
        self.posfile_cols = ['PETAL_LOC', 'DEVICE_LOC','TARGET_RA', 'TARGET_DEC','FIBERASSIGN_X',
        'FIBERASSIGN_Y','OFFSET_0','OFFSET_2','FIBER','EXPOSURE']
        self.petal_loc_to_id = {0:'4',1:'5',2:'6',3:'3',4:'8',5:'10',6:'11',7:'2',8:'7',9:'9'}

        self.exp_df = None
        self.connect_info = ' '

    def db_query(self, table_name, sample = None, table_type = 'telemetry'):
        """
        sample: int number of data points to take. If sample=60, it will sample every 60th data point.
        """
        try:
            self.conn = psycopg2.connect(host="desi-db", port="5442", database="desi_dev",
                  user="desi_reader", password="reader")
            self.connect_info = 'Connected to DB on desi server'
            if table_type == 'telemetry':
                query = pd.read_sql_query(f"SELECT * FROM {table_name} WHERE time_recorded >= '{self.start_date}' AND time_recorded <'{self.end_date}'",self.conn)
            elif table_type == 'exposure':
                #start, end = self.get_mjd_times([self.start_date, self.end_date], time_type='date')
                query = pd.read_sql_query(f"SELECT * FROM {table_name} WHERE date_obs >= '{self.start_date}' AND date_obs < '{self.end_date}'",self.conn)
            
            # Resample data. Most telemetry streams are taken every 1.5 seconds. 
            if isinstance(sample, int): 
                query = query[query.index % sample == 0]
            return query


        except:
            self.connect_info = "Cannot connect to DB on desi server. Cannot fetch data."
            return None

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

    def hex_and_adc(self, df):
        new_list = []
        for ix, row in df.iterrows():
            this_list = []
            for n in ['hex_trim','rot_rate','hex_status','rot_offset','rot_enabled','hex_position','rot_interval','hex_tweak']:
                try:
                    this_list.append(row['hexapod'][n])
                except:
                    this_list.append(np.nan)
            for n in ['status','adc_home1','adc_home2','adc_nrev1','adc_nrev2','adc_angle1','adc_angle2','adc_status','adc_status1','adc_status2','adc_rem_time1','adc_rem_time2']:
                try:
                    this_list.append(row['adc'][n])
                except:
                    this_list.append(np.nan)
            new_list.append(this_list)

        new_df = pd.DataFrame(np.vstack(new_list), columns =['hex_trim','rot_rate','hex_status','rot_offset','rot_enabled','hex_position','rot_interval','hex_tweak','adc_status','adc_home1','adc_home2','adc_nrev1','adc_nrev2','adc_angle1','adc_angle2','adc_status','adc_status1','adc_status2','adc_rem_time1','adc_rem_time2'] )
        return new_df

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

    def init_pos_file(self, fib):
        df = pd.DataFrame(columns = self.posfile_cols)
        df.to_csv('./instperfapp/data/per_fiber/{}.csv'.format(fib),index=False)

    def coord_data_to_pos_files(self, fib):
        if self.coord_files is None:
            self.get_coord_files()
            
        filen = './instperfapp/data/per_fiber/{}.csv'.format(fib)
        if not os.path.isfile(filen):
            self.init_pos_file(fib)

        pdf = pd.read_csv(filen)
        new_data = []
        for coord in self.coord_files:
            df = Table.read(coord,format='fits').to_pandas()
            df = df.merge(self.fiberpos, how='left',left_on=['PETAL_LOC','DEVICE_LOC'], right_on=['PETAL','DEVICE'])
            exposure = int(os.path.splitext(os.path.split(coord)[0])[0][-6:])
            ddf = df[df.FIBER == float(fib)]
            final_move = np.sort(fnmatch.filter(ddf.columns, 'OFFSET_*'))[-1]
            ddf = ddf[['PETAL_LOC', 'DEVICE_LOC','TARGET_RA', 'TARGET_DEC','FIBERASSIGN_X', 'FIBERASSIGN_Y','OFFSET_0',final_move,'FIBER']]
            ddf['EXPOSURE'] = exposure
            ddf = ddf.rename(columns={final_move:'OFFSET_FINAL'})
            new_data.append(ddf)

        new_df = pd.DataFrame(np.vstack(new_data),columns=self.posfile_cols)
        pdf = pd.concat([pdf,new_df])
        pdf.to_csv(filen, index=False)

    def add_posmove_telemetry(self, fib):
        filen = './instperfapp/data/per_fiber/{}.csv'.format(fib)
        pdf = pd.read_csv(filen)
        pdf.drop_duplicates(subset='EXPOSURE', keep='first',inplace=True)
        ptl_loc = int(np.unique(pdf.PETAL_LOC))
        dev = int(np.unique(pdf.DEVICE_LOC))
        telem_query = self.db_query('environmentmonitor_telescope', sample=60)
        ptl = self.petal_loc_to_id[ptl_loc]
        pos_query = pd.read_sql_query("SELECT * FROM positioner_moves_p{} WHERE device_loc = {} AND time_recorded >= '{}' AND time_recorded < '{}'".format(ptl,dev, self.start_date, self.end_date),self.conn)
        pos_df = self.convert_time_to_exp(list(np.unique(pdf.EXPOSURE)), pos_query)
        telem_df = self.convert_time_to_exp(list(np.unique(pdf.EXPOSURE)), telem_query)
        for df in [pdf, pos_df, telem_df]:
            df.reset_index(inplace=True, drop=True)
        df = pd.concat([pdf, telem_df, pos_df],axis=1)
        df.to_csv(filen, index=False)

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
        
