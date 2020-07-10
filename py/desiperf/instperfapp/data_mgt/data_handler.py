import pandas as pd
import numpy as np
import os, glob
import fnmatch
import matplotlib.pyplot as plt
from astropy.table import Table
import psycopg2
from datetime import datetime
from bokeh.models import ColumnDataSource

import pandas as pd
import numpy as np
import os, glob
import fnmatch
import matplotlib.pyplot as plt
from astropy.table import Table
import psycopg2
from datetime import datetime
from astropy.time import Time
from astropy.io import fits

from bokeh.models import ColumnDataSource
from data_mgt.data_general import DataSource


class DataHandler(object):
    def __init__(self, start_date = '20200101', end_date = '20200316', option = 'no_update'):
        self.start_date = start_date
        self.end_date = end_date
        self.DS = DataSource(self.start_date, self.end_date)
        self.option = option #OPTIONS: no_update, update, init(ialize)
        self.data_columns = [ 'skyra', 'skydec',  'exptime', 'tileid', 
                            'airmass', 'mountha', 'zd', 'mountaz', 'domeaz', 
                            'zenith', 'mjd_obs', 'moonra', 'moondec', 
                            'EXPOSURE', 'max_blind', 'max_blind_95', 
                            'rms_blind', 'rms_blind_95', 'max_corr',
                            'max_corr_95', 'rms_corr', 'rms_corr_95', 
                            'mirror_temp', 'truss_temp', 'air_temp', 
                            'mirror_avg_temp', 'wind_speed', 'wind_direction', 
                            'humidity', 'pressure', 'temperature', 'dewpoint', 
                            'shutter_open', 'exptime_sec', 'psf_pixels', 
                            'guide_meanx', 'guide_meany','guide_meanx2', 
                            'guide_meany2', 'guide_meanxy', 'guide_maxx',
                            'guide_maxy', 'guider_combined_x', 
                            'guider_combined_y']
        hdu = fits.open('./instperfapp/data/fiberpos.fits')
        self.fiberpos = Table(hdu[1].data).to_pandas()
        #print(self.fiberpos)

    def get_focalplane_data(self):
        if self.option == 'no_update':
            init_data = Table.read('./instperfapp/data/per_timestamp.fits', format='fits').to_pandas() 
            self.focalplane_source = ColumnDataSource(init_data)

        elif self.option == 'init':
            pass

        elif self.option == 'update':
            pass

    def get_qa_values(self, exposure_array):
       # This is currently only available on NERSC. The files on the desi server do not have the PER_AMP.
       qa_files = []
       #for row in exposure_array:
       #    date = np.datetime_as_string(row['date_obs'],unit='D').replace('-','') #prob need to manipulate
       #    exp = str(int(row['id'])).zfill(8)
       for date in np.unique(exposure_array['date_obs']):
           date = np.datetime_as_string(date, unit='D').replace('-','')
           qa_files.append(glob.glob('/exposures/nightwatch/{}/*/qa-*.fits'.format(date)))
       qa_files = np.hstack(qa_files)
       D = []
       for qa in qa_files:
           try:
               hdu = fits.open(qa)
               try:
                   df = Table(hdu['PER_AMP']).to_pandas()
                   D.append(df[['NIGHT','EXPID','SPECTRO','CAM','AMP','READNOISE','BIAS','COSMICS_RATE']])
               except:
                   pass
           except:
               print(qa)

       df = pd.DataFrame(np.vstack(D), columns = ['NIGHT','EXPID','SPECTRO','CAM','AMP','READNOISE','BIAS','COSMICS_RATE'])
       return df

    def get_detector_data(self):
        """
        OPTIONS: no_update, update, init(ialize)
        Don't know how to split up data yet. Will just start with a few files and go from there
        """
        if self.option == 'no_update':
            files = glob.glob('./instperfapp/data/detector/det_qa_*.csv')
            df = pd.concat([pd.read_csv(f) for f in files])
            self.detector_source = ColumnDataSource(df)

        elif self.option == 'init':

            exposure_array = self.DS.get_exposures_in_range() #rec array with id, date_obs
            qa_df = self.get_qa_values(exposure_array)
            spec_df = self.DS.db_query('spectrographs_sensors')
            spec_df = spec_df[spec_df.index % 60 == 0] #Data taken every 1.5 seconds cut to every ~2 minutes. Too much and takes too much time. Can change the 60 to whatever number
            new_spec_df = self.DS.telemetry_for_exposures(exposure_array['id'],spec_df)

            df = pd.merge(left=qa_df, right=new_spec_df, left_on = 'EXPID', right_on='EXPID',how='inner')
            dfs = np.array_split(df,4) #How small??
            for i, df_ in enumerate(dfs):
                df_.to_csv('./instperfapp/data/detector/det_qa_{}.csv'.format(i))
            self.detector_source = ColumnDataSource(df)

        elif self.option == 'update':
            pass
            #Open current files
            #Figure out which dates are needed
            #Get exposure list for new ones
            #Get QA data
            #Get exp data
            #make new file

    def run(self):
        self.get_detector_data() #self.detector_source
        self.get_focalplane_data() #self.focalplane_source


    #######EVERYTHING BELOW THIS ISN"T READY TO USE YET#############

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

