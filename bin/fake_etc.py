#!/usr/bin/env python
'''
Create fake ETC telemetry for testing
'''

import numpy as np
import pandas as pd

nexps = 10 
rowsperexp = 10
nrows = nexps * rowsperexp

expid1 = 3900

outfile = 'etc_output.csv'

# conn = psycopg2.connect(host="desi-db", port="5442", database="desi_dev", user="desi_reader", password="reader")
# etcquery = pd.read_sql_query(f"SELECT * FROM etc_telemetry WHERE time_recorded > '2020-01-23' and time_recorded < '2020-03-16'", conn)
# etcquery.columns
# Index(['etc_telemetry', 'expid', 'time_remaining', 'estimated_snr', 'goal_snr',
#        'will_not_finish', 'about_to_finish', 'seeing', 'transparency',
#        'skylevel', 'start_time', 'max_exposure_time', 'cosmics_split_time',
#        'last_updated', 'time_recorded', 'dos_instance', 'row_status',
#        'row_status_time', 'row_status_user'],
#       dtype='object')

dtype = [('etc_telemetry', 'int32'), 
    ('expid', 'int32'), 
    ('estimated_snr', 'float32'), 
    ('goal_snr', 'float32'), 
    ('will_not_finish', 'bool'), 
    ('about_to_finish', 'bool'), 
    ('seeing', 'float32'), 
    ('transparency', 'float32'), 
    ('skylevel', 'float32'), 
    ('start_time', 'datetime64[s]'), 
    ('max_exposure_time', 'float32'), 
    ('cosmics_split_time', 'float32'),
    ('last_updated', 'datetime64[s]'),
    ('time_recorded', 'datetime64[s]'),
    ('dos_instance', 'int32'),
    ('row_status', 'bool'),
    ('row_status_time', 'float32'),
    ('row_status_user', 'float32')]

values = np.zeros(nrows, dtype=dtype)
index = [str(i) for i in range(1, len(values)+1)]

df = pd.DataFrame(values, index=index)

expids = np.zeros(nrows, dtype=np.int32) + expid1
expid = 0
for i in range(1, nrows): 
    if i % rowsperexp == 0: 
        expid += 1  
    expids[i] += expid
df['expid'] = expids

df['estimated_snr'] = 3.
df['goal_snr'] = 5.

for i in range(1, nrows): 
    if (i + 1) % rowsperexp == 0: 
        df.loc[df.index[i], 'about_to_finish'] = True

tt = np.datetime64('2020-03-01T00:00')
df.loc[df.index[0], 'start_time'] = tt
for i in range(1, nrows): 
    if i % rowsperexp == 0: 
        tt += np.timedelta64(30, 'm')
    df.loc[df.index[i], 'start_time'] = tt

df['seeing'] = np.random.normal(1.05, 0.05, nrows)
df['transparency'] = np.clip(np.random.normal(0.9, 0.1, nrows), None, 1.)
df['skylevel'] = np.random.normal(10, 0.1, nrows)

df['last_updated'] = '2020-04-01 00:00:00.00'
df['time_recorded'] = '2020-03-31 00:00:00.00'
df['max_exposure_time'] = 1200.

df.to_csv(outfile)

print("Put output file {0} in ../desiperf/py/desiperf/instperfapp/data/".format(outfile))
