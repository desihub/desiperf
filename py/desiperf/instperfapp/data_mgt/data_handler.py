""" This class pulls data for the Application. It only loads the data

"""

import pandas as pd
import numpy as np
import os, glob
from datetime import datetime
from astropy.time import Time

from bokeh.models import ColumnDataSource


class DataHandler(object):
    def __init__(self, start_date = '20200123', end_date = '20200316', option = 'no_update'):
        self.start_date = start_date
        self.end_date = end_date

        self.data_dir = os.path.join(os.getcwd(),'instperfapp','data')
        self.pos_dir = os.path.join(self.data_dir, 'per_fiber')
        self.fp_dir = os.path.join(self.data_dir, 'focalplane')
        self.det_dir = os.path.join(self.data_dir, 'detector')

        self.fiberpos = pd.read_csv('./instperfapp//data/fiberpos.csv')

        self.FIBERS = [1235 , 2561, 2976, 3881, 4844, 763, 2418, 294, 3532, 4731, 595]

    def get_focalplane_data(self):
        files = glob.glob(os.path.join(self.fp_dir, 'fpa_data_*.csv')) 
        fp_df = pd.concat([pd.read_csv(f, low_memory=False) for f in files])
        fp_df = self.get_datetime(fp_df)
        fp_df['obstype'] = fp_df['obstype'].astype('str').str.upper() 
        fp_df = fp_df[(fp_df.datetime >= self.start_date)&(fp_df.datetime <= self.end_date)]
        fp_df.columns = [x.upper() for x in fp_df.columns]
        fp_df = fp_df.loc[:,~fp_df.columns.duplicated()]
        self.focalplane_source = ColumnDataSource(fp_df)

    def get_detector_data(self):
        files = glob.glob(os.path.join(self.det_dir, 'qa_data_*.csv'))
        spec_df = pd.concat([pd.read_csv(f, low_memory=False) for f in files])
        spec_df = self.get_datetime(spec_df)
        spec_df['obstype'] = spec_df['obstype'].astype('str').str.upper() 
        spec_df = spec_df[(spec_df.datetime >= self.start_date)&(spec_df.datetime <= self.end_date)]
        spec_df.columns = [x.upper() for x in spec_df.columns]
        self.detector_source = ColumnDataSource(spec_df)

    def get_positioner_data(self):
        # This data is loaded from the positioner page for individual positioners.
        if self.FIBERS == 'all':
            self.FIBERS = np.linspace(0,5000,5000)

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



    def run(self):
        self.get_focalplane_data() #self.focalplane_source
        self.get_detector_data() #self.detector_source
        self.get_positioner_data()

