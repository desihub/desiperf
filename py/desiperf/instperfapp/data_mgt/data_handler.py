""" This class pulls data for the Application. It only loads the data

"""

import pandas as pd
import numpy as np
import os, glob
from datetime import datetime
from astropy.time import Time
from astropy.table import Table

from bokeh.models import ColumnDataSource

from data_mgt.get_fp_data import FPData
from data_mgt.get_spec_data import SPECData
from data_mgt.get_pos_data import POSData


class DataHandler(object):
    def __init__(self, start_date = '20200123', end_date = '20210525', option = 'no_update'):
        self.option = option
        self.start_date = start_date
        self.end_date = end_date
        print('Start: {}, End: {}'.format(self.start_date, self.end_date))

        self.data_dir = os.environ['DATA_DIR']
        self.pos_dir = os.path.join(self.data_dir, 'positioners')
        self.fp_dir = os.path.join(self.data_dir, 'focalplane')
        self.det_dir = os.path.join(self.data_dir, 'detector')

        self.fiberpos = pd.read_csv('./instperfapp//data_mgt/fiberpos.csv')

        self.FIBERS = [1235 , 2561, 2976, 3881, 4844, 763, 2418, 294, 3532, 4731, 595]

    def prepare_focalplane_source(self):
            

        fpfile = os.path.join(self.fp_dir, 'fpa_all.fits.gz')
        print('Focal Plane Data Coming from {}'.format(fpfile))
        fptab = Table.read(fpfile)
        fp_df = fptab.to_pandas()

        if self.option == 'update':
            time = fp_df[fp_df.night < 1e+20].night
            last_end = int(max(time))
            fpd = FPData(last_end, self.end_date, 'update')            
            print(last_end, self.end_date)
            fpd.run()
            print("Updated FP Data")
            fp_df = Table.read(fpfile).to_pandas()

        fp_df = self.get_datetime(fp_df)
        fp_df['obstype'] = fp_df['obstype'].str.decode("utf-8")
        fp_df['program'] = fp_df['program'].str.decode("utf-8")

        fp_df = fp_df[(fp_df.datetime >= self.start_date)&(fp_df.datetime <= str((int(self.end_date)+1)))]
        fp_df.columns = [x.upper() for x in fp_df.columns]
        fp_df = fp_df.loc[:,~fp_df.columns.duplicated()]

        fp_df['FOCUS'] = fp_df['FOCUS'].str.decode("utf-8")
        fp_df['FOCUS'] = fp_df['FOCUS'].map(lambda x: x.lstrip('[').rstrip(']'))

        fp_df['FOCUS_X'] = fp_df['FOCUS'].str.split(', ').str[0]
        fp_df['FOCUS_X'] = pd.to_numeric(fp_df['FOCUS_X'],errors='coerce')

        fp_df['FOCUS_Y'] = fp_df['FOCUS'].str.split(', ').str[1]
        fp_df['FOCUS_Y'] = pd.to_numeric(fp_df['FOCUS_Y'],errors='coerce')

        fp_df['FOCUS_Z'] = fp_df['FOCUS'].str.split(', ').str[2]
        fp_df['FOCUS_Z'] = pd.to_numeric(fp_df['FOCUS_Z'],errors='coerce')

        fp_df['FOCUS_TIP'] = fp_df['FOCUS'].str.split(', ').str[3]
        fp_df['FOCUS_TIP'] = pd.to_numeric(fp_df['FOCUS_TIP'],errors='coerce')

        fp_df['FOCUS_TILT'] = fp_df['FOCUS'].str.split(', ').str[4]
        fp_df['FOCUS_TILT'] = pd.to_numeric(fp_df['FOCUS_TILT'],errors='coerce')

        fp_df['FOCUS_ROT'] = fp_df['FOCUS'].str.split(', ').str[5]
        fp_df['FOCUS_ROT'] = pd.to_numeric(fp_df['FOCUS_ROT'],errors='coerce')

        self.focalplane_source = ColumnDataSource(fp_df)

    def prepare_detector_source(self):

        specfile = os.path.join(self.det_dir, 'spec_all.fits.gz') 
        print('Spectrograph Data Coming from {}'.format(specfile))
        spectab = Table.read(specfile)
        spec_df = spectab.to_pandas()

        if self.option == 'update':
            time = spec_df[spec_df.night < 1e+20].night
            last_end = int(max(time))
            specd = SPECData(last_end, self.end_date, 'update')
            print(last_end, self.end_date)
            specd.run()
            print("Updated Spec Data")

        spec_df['date_obs'] = spec_df['date_obs'].str.decode("utf-8") #[x.decode("utf-8") for x in list(spec_df['date_obs'])] #.str.decode("utf-8")
        spec_df['CAM'] = spec_df['CAM'].str.decode("utf-8")
        spec_df['obstype'] = spec_df['obstype'].str.decode("utf-8")
        spec_df['program'] = spec_df['program'].str.decode("utf-8")
        spec_df = self.get_datetime(spec_df)

        spec_df = spec_df[(spec_df.night >= int(self.start_date))&(spec_df.night <= (int(self.end_date)+1))]

        spec_df.columns = [x.upper() for x in spec_df.columns]
        self.detector_source = ColumnDataSource(spec_df)

    def prepare_positioner_source(self):
        if self.option == 'update':
            print('Skipping pos this time')
            #pos_df = pd.read_csv('6830.csv')
            #time = pd.to_datetime(pos_df.date_obs_x)
            #last_date = max(time).strftime('%Y%m%d')
            #pos = POSData(last_date, self.end_date, 'update')
            #pos.run()

    def get_datetime(self, df):
        if 'date_obs' in list(df.columns):
            times = df['date_obs'].str.decode("utf-8") #[x.decode("utf-8") for x in df.date_obs]
            datetimes = pd.to_datetime(times)
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
        self.prepare_focalplane_source() #self.focalplane_source
        self.prepare_detector_source() #self.detector_source
        self.prepare_positioner_source()
