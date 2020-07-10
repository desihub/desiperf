
import pandas as pd
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

        self.exp_df = None



    def db_query(self, table_name, table_type = 'telemetry'):
        self.conn = psycopg2.connect(host="desi-db", port="5442", database="desi_dev",
                  user="desi_reader", password="reader")
        if table_type == 'telemetry':
            query = pd.read_sql_query(f"SELECT * FROM {table_name} WHERE time_recorded >= '{self.start_date}' AND time_recorded <'{self.end_date}'",self.conn)
        elif table_type == 'exposure':
            #start, end = self.get_mjd_times([self.start_date, self.end_date], time_type='date')
            query = pd.read_sql_query(f"SELECT * FROM {table_name} WHERE date_obs >= '{self.start_date}' AND date_obs < '{self.end_date}'",self.conn)

        return query

    def get_exp_df(self):
        self.exp_df = self.db_query('exposure',table_type='exposure')

    def align_datasets(self, df_with_exp, df_with_time):
        for col in ['EXPOSURE','EXPID']:
            if col in df_with_exp.columns:
                exposures = [int(exp) for exp in np.unique(df_with_exp[col])]

        df_with_time = self.telemetry_for_exposures(exposures, df_with_time)
        df_with_exp.reset_index(inplace=True, drop=True)
        df_with_time.reset_index(inplace=True,drop=True)
        combined_df = pd.concat([df_with_exp, df_with_time], axis=1)
        return combined_df

    def telemetry_for_exposures(self, exp_list, tele_df):
        print(datetime.now())
        if self.exp_df is None:
            self.get_exp_df()
        print(datetime.now())
        times = self.get_mjd_times(tele_df.time_recorded)
        print(datetime.now())
        idx = []
        for t in self.exp_df[self.exp_df.id.isin(exp_list)].mjd_obs:
            dt = [np.abs(tt-t) for tt in times]
            idx.append(np.argmin(dt))
        new_df = tele_df.iloc[idx]
        new_df['EXPID'] = list(self.exp_df[self.exp_df.id.isin(exp_list)].id)
        print(datetime.now())
        return new_df

    def get_mjd_times(self, time_list, time_type = 'Timestamp'):
        if time_type == 'Timestamp':
            times = [Time(t).mjd for t in time_list]
        elif time_type == 'date':
            times = [Time(datetime.strptime(t, '%Y%m%d')).mjd for t in time_list]

        return times

    def get_exposures_in_range(self):

        if self.exp_df is None:
            self.get_exp_df()
        df = self.exp_df[['id','date_obs']]
        return df.to_records()