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
    def __init__(self, start_date = '20200123', end_date = '20200316', option = 'no_update'):
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

        self.data_dir = os.path.join(os.getcwd(),'instperfapp','data')
        self.pos_dir = os.path.join(self.data_dir, 'per_fiber')
        self.fp_dir = os.path.join(self.data_dir, 'focalplane')
        self.det_dir = os.path.join(self.data_dir, 'detector')
        self.fiberpos = self.DS.fiberpos
        self.etc_data = pd.read_csv(os.path.join(self.data_dir, 'etc_output.csv'))
        self.FIBERS = [1235 , 2561, 2976, 3881, 4844, 763, 2418, 294, 3532, 4731, 595]

    def get_focalplane_data(self):
        if self.option == 'no_update':
            files = glob.glob(os.path.join(self.fp_dir, 'fpa_data_*.csv')) 
            fp_df = pd.concat([pd.read_csv(f, low_memory=False) for f in files])
            fp_df = self.get_datetime(fp_df)
            fp_df = fp_df[(fp_df.datetime >= self.start_date)&(fp_df.datetime <= self.end_date)]
            self.focalplane_source = ColumnDataSource(fp_df)

        elif self.option == 'init':
            telescope_telem = self.DS.db_query('environmentmonitor_telescope', sample=60)
            tower_telem = self.DS.db_query('environmentmonitor_tower', sample=60)
            fvc_telem = self.DS.db_query('fvc_camerastatus',sample=60)
            guide1 = self.DS.db_query('guider_summary')
            guide2 = self.DS.db_query('guider_centroids')

            pos_df = self.DS.fp_pos_accuracy()
            pos_df.drop_duplicates(subset='EXPOSURE', keep='first',inplace=True)
            pos_df = pos_df[pos_df.EXPOSURE.isin(self.DS.full_exp_list.id)]
            fp_exposures = np.unique(pos_df.EXPOSURE) #this has exposures

            telescope_df = self.DS.convert_time_to_exp(fp_exposures, telescope_telem)
            tower_df = self.DS.convert_time_to_exp(fp_exposures, tower_telem)
            fvc_df = self.DS.convert_time_to_exp(fp_exposures, fvc_telem)
            guide1_df = self.DS.convert_time_to_exp(fp_exposures, guide1)
            guide2_df = self.DS.convert_time_to_exp(fp_exposures, guide2)
            exp_df = self.DS.exp_df[self.DS.exp_df.id.isin(fp_exposures)]
            hex_adc_df = self.DS.hex_and_adc(exp_df)
            for df in [exp_df, telescope_df, tower_df, fvc_df, guide1_df, guide2_df, hex_adc_df, pos_df]:
                df.reset_index(inplace=True, drop=True)
            fp_df = pd.concat([exp_df, pos_df,telescope_df,tower_df,fvc_df,guide1_df,guide2_df],axis=1)
            dfs = np.array_split(fp_df,4) #How small??
            for i, df_ in enumerate(dfs):
                df_.to_csv(os.path.join(self.fp_dir, 'fpa_data_{}.csv'.format(i)), index=False)
            self.focalplane_source = ColumnDataSource(fp_df)


        elif self.option == 'update':
            pass

    def get_detector_data(self):
        """
        OPTIONS: no_update, update, init(ialize)
        Don't know how to split up data yet. Will just start with a few files and go from there
        """
        if self.option == 'no_update':
            files = glob.glob(os.path.join(self.det_dir, 'qa_data_*.csv'))
            df = pd.concat([pd.read_csv(f, low_memory=False) for f in files])
            df = self.get_datetime(df)
            df = df[(df.datetime >= self.start_date)&(df.datetime <= self.end_date)]
            self.detector_source = ColumnDataSource(df)

        elif self.option == 'init':

            det_cols = ['NIGHT','EXPID','SPECTRO','CAM','AMP','READNOISE','BIAS','COSMICS_RATE']
            qa_df = self.DS.get_qa_data('PER_AMP', det_cols)
            qa_exposures = np.unique(qa_df.EXPID)
            spec_df = self.DS.db_query('spectrographs_sensors', sample=60)
            new_spec_df = self.DS.convert_time_to_exp(qa_exposures, spec_df)

            df = pd.merge(left=qa_df, right=new_spec_df, left_on = 'EXPID', right_on='EXPID',how='inner')
            dfs = np.array_split(df,4) #How small??
            for i, df_ in enumerate(dfs):
                df_.to_csv(os.path.join(self.det_dir,'qa_data_{}.csv'.format(i)))
            self.detector_source = ColumnDataSource(df)

        elif self.option == 'update':
            pass
            #Open current files
            #Figure out which dates are needed
            #Get exposure list for new ones
            #Get QA data
            #Get exp data
            #make new file

    def get_datetime(self, df):
        if 'date_obs' in list(df.columns):
            datetimes = pd.to_datetime(df.date_obs)
        elif 'mjd_obs' in list(df.columns):
            dt = [Time(t, format='mjd', scale='utc').datetime for t in list(df.mjd_obs)]
            datetimes = pd.to_datetime(dt)
        elif 'time_recorded' in list(df.columns):
            datetimes = pd.to_datetime(df.time_recorded)
        else:
            datetimes = np.zeros(len(df))

        df['datetime'] = datetimes
        return df


    def get_positioner_data(self):
        if self.FIBERS == 'all':
            self.FIBERS = np.linspace(0,5000,5000)

        if self.option == 'no_update':
            pass
        elif self.option == 'init':
            for fib in self.FIBERS:
                self.DS.coord_data_to_pos_files(fib)
                self.DS.add_posmove_telemetry(fib)
        elif self.option == 'update':
            pass

    def run(self):
        self.get_focalplane_data() #self.focalplane_source
        self.get_detector_data() #self.detector_source
        self.get_positioner_data()
        self.etc_source = ColumnDataSource(self.etc_data)

