#!/usr/bin/env python
  
import os, sys
import numpy as np
from astropy.io import fits
from glob import glob
import argparse
import matplotlib.pyplot as plt
from astropy.time import Time
import json
import ephem
import psycopg2
import pandas as pd

def read_json(filename: str):
    with open(filename) as fp:
        return json.load(fp)

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                        description="""Generate nightly efficiency 
                        statistics, e.g. try ./nightstats.py -n 20201221""") 

parser.add_argument('-n','--night', type=str, default="20201215", required=False,
                    help='Night to analyze')

parser.add_argument('-c','--clobber', action='store_true', default=False, 
                    required=False,
                    help='Clobber (overwrite) output if it already exists?')

parser.add_argument('-v','--verbose', action='store_true', default=False, 
                    required=False,
                    help='Provide verbose output?')

args = parser.parse_args()

night = args.night

# Find the nightly data (just distinguish between kpno and cori): 
kpnoroot = '/exposures/desi'
coriroot = '/global/cfs/cdirs/desi/spectro/data/'

if os.path.isdir(kpnoroot):
    nightdir = os.path.join(kpnoroot, night) 
    dbhost = 'desi-db'
    dbport = '5442'
elif os.path.isdir(coriroot): 
    nightdir = os.path.join(coriroot, night) 
    dbhost = 'db.replicator.dev-cattle.stable.spin.nersc.org'
    dbport = '60042'
else: 
    print("Error: root data directory not found")
    print("  Looked for {0} and {1}".format(kpnoroot, coriroot))
    exit(-1)
        
# matplotlib settings 
SMALL_SIZE = 14
MEDIUM_SIZE = 16
BIGGER_SIZE = 18

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=BIGGER_SIZE)    # fontsize of the x and y labels
plt.rc('lines', linewidth=2)
plt.rc('axes', linewidth=2)
plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=MEDIUM_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title


# Names for output json files: 
specdatafile = "specdata" + night + ".json"
guidedatafile = "guidedata" + night + ".json"
outplot = "nightstats" + night + ".png" 

# See if json files for this night already exist: 
if os.path.isfile(specdatafile) and os.path.isfile(guidedatafile) and not args.clobber: 
    specdata = read_json(specdatafile)
    guidedata = read_json(guidedatafile)
else: 
    # List of all directories: 
    expdirs = glob(nightdir + "/*")
    # List of all expids: 
    expids = expdirs.copy()
    for i in range(len(expdirs)):
        expids[i] = expdirs[i][expdirs[i].find('000')::]
    # Get all spec observations: 
    specdata = {}
    for expid in expids: 
        tmpdir = os.path.join(nightdir, expid)
        scifiles = (glob(tmpdir + "/desi*"))
        if len(scifiles) > 0:  
           hhh = fits.open(scifiles[0])
           specdata[expid] = {}
           specdata[expid]['DATE-OBS'] = Time(hhh[1].header['DATE-OBS']).mjd
           specdata[expid]['OBSTYPE'] = hhh[1].header['OBSTYPE']
           specdata[expid]['FLAVOR'] = hhh[1].header['FLAVOR']
           specdata[expid]['PROGRAM'] = hhh[1].header['PROGRAM']
           specdata[expid]['EXPTIME'] = hhh[1].header['EXPTIME']
           try: 
               specdata[expid]['DOMSHUTU'] = hhh[1].header['DOMSHUTU']
           except KeyError: 
               specdata[expid]['DOMSHUTU'] = 'None'
           try: 
               specdata[expid]['PMCOVER'] = hhh[1].header['PMCOVER']
           except KeyError: 
               specdata[expid]['PMCOVER'] = 'None'
    with open(specdatafile, 'w') as fp:
        json.dump(specdata, fp) 
    if args.verbose: 
        print("Wrote", specdatafile) 
    # 
    # Get all guide observations: 
    #  
    guidedata = {}
    for expid in expids: 
        tmpdir = os.path.join(nightdir, expid)
        guidefiles = (glob(tmpdir + "/guide-" + expid + ".fits.fz"))
        if len(guidefiles) > 0:  
           hhh = fits.open(guidefiles[0])
           guidedata[expid] = {}
           t1 = Time(hhh['GUIDE0T'].data[0]['DATE-OBS']).mjd
           t2 = Time(hhh['GUIDE0T'].data[-1]['DATE-OBS']).mjd
           guidedata[expid]['GUIDE-START'] = t1 
           guidedata[expid]['GUIDE-STOP'] = t2 
           try: 
               guidedata[expid]['DOMSHUTU'] = hhh[0].header['DOMSHUTU']
           except KeyError: 
               guidedata[expid]['DOMSHUTU'] = 'None'
           guidedata[expid]['PMCOVER'] = hhh[0].header['PMCOVER']
           try: 
               guidedata[expid]['OBSTYPE'] = hhh[0].header['OBSTYPE']
           except KeyError: 
               guidedata[expid]['OBSTYPE'] = 'None' 
           try: 
               guidedata[expid]['FLAVOR'] = hhh[0].header['FLAVOR']
           except KeyError: 
               guidedata[expid]['FLAVOR'] = 'None'
           try: 
               guidedata[expid]['EXPTIME'] = hhh[0].header['EXPTIME']
           except KeyError: 
               guidedata[expid]['EXPTIME'] = 0.
    with open(guidedatafile, 'w') as fp:
        json.dump(guidedata, fp) 
    if args.verbose: 
        print("Wrote", guidedatafile) 


# Determine the MJD for the start of the night, convert to UT 
mjds = np.zeros(len(specdata), dtype=float)
for i, item in enumerate(specdata.keys()):
    mjds[i] = specdata[item]['DATE-OBS']
    
startdate = int( mjds.max() ) 
starttime = (mjds.min() - startdate)*24

# Establish (long, lat) to calculate twilight
t = Time(startdate, format='mjd')
desi = ephem.Observer()
desi.lon = '-111.59989'
desi.lat = '31.96403'
desi.elev = 2097.
desi.pressure = 0
desi.date = t.strftime('%Y/%m/%d 7:00')

# Calculate astronomical twilight times
desi.horizon = '-18'
beg_twilight=desi.previous_setting(ephem.Sun(), use_center=True) # End astro twilight
end_twilight=desi.next_rising(ephem.Sun(), use_center=True) # Begin astro twilight
twibeg = Time( beg_twilight.datetime(), format='datetime')
twiend = Time( end_twilight.datetime(), format='datetime')

# Calculate the start and duration for the science observations:
science_start = []
science_width = []
for item in specdata: 
    if specdata[item]['OBSTYPE'] == 'SCIENCE' and specdata[item]['FLAVOR'] == 'science' and 'Dither' not in specdata[item]['PROGRAM'] and specdata[item]['DOMSHUTU'] == 'open' and specdata[item]['PMCOVER'] == 'open':
        science_start.append( (specdata[item]['DATE-OBS'] - startdate)*24. )
        science_width.append( specdata[item]['EXPTIME']/3600. )

# Separately account for time with dither tests
dither_start = []
dither_width = []
for item in specdata:
    if specdata[item]['OBSTYPE'] == 'SCIENCE' and specdata[item]['FLAVOR'] == 'science' and 'Dither' in specdata[item]['PROGRAM']:
        dither_start.append( (specdata[item]['DATE-OBS'] - startdate)*24. )
        dither_width.append( specdata[item]['EXPTIME']/3600. )

# Times for guiding: 
guide_start = []
guide_width = []
for item in guidedata:
    if guidedata[item]['OBSTYPE'] == 'SCIENCE' and guidedata[item]['FLAVOR'] == 'science' and guidedata[item]['PMCOVER'] == 'open' and guidedata[item]['DOMSHUTU'] == 'open':
        guide_start.append( (guidedata[item]['GUIDE-START'] - startdate)*24. )
        guide_width.append( (guidedata[item]['GUIDE-STOP'] - guidedata[item]['GUIDE-START'])*24. )
        
# Calculate times for arcs
arc_start = []
arc_width = []
for item in specdata:
    if specdata[item]['OBSTYPE'] == 'ARC' and specdata[item]['FLAVOR'] == 'science':
        arc_start.append( (specdata[item]['DATE-OBS'] - startdate)*24. )
        arc_width.append( specdata[item]['EXPTIME']/3600. )

# Calculate times for flats
flat_start = []
flat_width = []
for item in specdata:
    if specdata[item]['OBSTYPE'] == 'FLAT' and specdata[item]['FLAVOR'] == 'science':
        flat_start.append( (specdata[item]['DATE-OBS'] - startdate)*24. )
        flat_width.append( specdata[item]['EXPTIME']/3600. )

# Connect to the DB to get additional telemetry:
conn = psycopg2.connect(host=dbhost, port=dbport, database="desi_dev", user="desi_reader", password="reader")
query_start = twibeg - (3./24.)
query_stop = twiend + (3./24.) 

# Get dome status: 
domedf = pd.read_sql_query(f"SELECT dome_timestamp,shutter_upper,mirror_cover FROM environmentmonitor_dome WHERE time_recorded >= '{query_start}' AND time_recorded < '{query_stop}'", conn)
dome = domedf.to_records()
dome['dome_timestamp'] = np.array([Time(t) for t in dome['dome_timestamp']])
dometime = np.array([ (Time(t).mjd - startdate)*24 for t in dome['dome_timestamp']])
dome_open = np.array([t for t in dome['shutter_upper']], dtype=bool)
mirror_open = np.array([t for t in dome['mirror_cover']], dtype=bool)

# Get guider fwhm data: 
guidedf = pd.read_sql_query(f"SELECT time_recorded,seeing,meanx,meany FROM guider_summary WHERE time_recorded >= '{query_start}' AND time_recorded < '{query_stop}'", conn)
guide = guidedf.to_records()
guidetime = (Time(guide['time_recorded']).mjd - startdate)*24

# Compute total science and guiding time 
 # in hours
twibeg_hours = 24.*(twibeg.mjd - startdate)
twiend_hours = 24.*(twiend.mjd - startdate)
twitot_hours = twiend_hours - twibeg_hours 
# # as a percent of dark time
#guiding_percent = 100.*np.sum(guide_width)/twitot_hours
#science_percent = 100.*np.sum(science_width)/twitot_hours

# Compute total time open between twilights: 
nmask = dometime > twibeg_hours
nmask = nmask*(dometime < twiend_hours)
dmask = nmask*dome_open
open_fraction = np.sum(nmask)/np.sum(dmask)
        
# Calculate the total science time between twilights: 
science_hours = 0.
for i in range(len(science_start)): 
    s1 = science_start[i]
    s2 = s1 + science_width[i]
    if s1 <= twibeg_hours and s2 >= twibeg_hours: 
        science_hours += s2-twibeg_hours
    elif s1 >= twibeg_hours and s2 <= twiend_hours: 
        science_hours += s2-s1
    elif s1 <= twiend_hours and s2 >= twiend_hours: 
        science_hours += s1-twiend_hours

# Calculate the total guide time between twilights: 
guide_hours = 0.
for i in range(len(guide_start)): 
    g1 = guide_start[i]
    g2 = g1 + guide_width[i]
    if g1 <= twibeg_hours and g2 >= twibeg_hours: 
        guide_hours += g2-twibeg_hours
    elif g1 >= twibeg_hours and g2 <= twiend_hours: 
        guide_hours += g2-g1
    elif g1 <= twiend_hours and g2 >= twiend_hours: 
        guide_hours += g1-twiend_hours

# Total time dome was open between twilights
twitot_dome_hours = open_fraction*twitot_hours

# Percent of time dome was open between twilights with science, guide exposures
science_fraction = science_hours/twitot_dome_hours
guide_fraction = guide_hours/twitot_dome_hours
# Total number of each type of observing block
science_num = len(science_width)
guide_num = len(guide_width)

if args.verbose: 
    print("Total hours between twilights: {0:.1f}".format(twitot_dome_hours))
    print("  Open: {0:.1f}%".format(100.*open_fraction))
    print("  Science: {0:.1f}% ({1})".format(100.*science_fraction, science_num))
    print("  Guide: {0:.1f}% ({1})".format(100.*guide_fraction, guide_num))

fig, ax1 = plt.subplots(figsize=(14,4))
barheight = 0.10

y_guide = 0.25
y_science = 0.75

ymin = -0.05
ymax = 1.25

# Draw time sequence for spectroscopy, guiding
ax1.barh(y_science, science_width, 2*barheight, science_start, align='center', color='b')
ax1.barh(y_science, dither_width, 2*barheight, dither_start, align='center', color='c')
ax1.barh(y_guide, guide_width, barheight, guide_start, align='center', color='b')

# Twilight
ax1.plot([twibeg_hours, twibeg_hours], [ymin, ymax], 'k--')
ax1.plot([twiend_hours, twiend_hours], [ymin, ymax], 'k--')

# Populate in case no data were obtained in each category
if len(science_start) == 0: 
    science_start.append(xlab + 4.)
    science_width.append(0.) 

if len(guide_start) == 0: 
    guide_start.append(xlab + 4.)
    guide_width.append(0.)

# Default label locations
y1, y2 = ax1.get_ylim()
xlab = float(twibeg_hours - 4.)
ylab1 = y1 + 0.9*(y2-y1)
ylab2 = y1 + 0.8*(y2-y1)
ylab3 = y1 + 0.7*(y2-y1)
ylab4 = y1 + 0.6*(y2-y1)
lab1 = "Night: {0:.1f} hrs".format(twitot_hours)
lab2 = "Open: {0:.1f} %".format(100.*open_fraction)
lab3 = "Science: {0:.1f}% ({1})".format(100.*science_fraction, science_num)
lab4 = "Guide: {0:.1f}% ({1})".format(100.*guide_fraction, guide_num)
ax1.text(xlab, ylab1, lab1, va='center')
ax1.text(xlab, ylab2, lab2, va='center')
ax1.text(xlab, ylab3, lab3, va='center')
ax1.text(xlab, ylab4, lab4, va='center')

# Dome status
ax1.plot(dometime, dome['shutter_upper'], ':')

# Adjust limits
ax1.set_ylim(ymin, ymax)   
ax1.set_xlim(twibeg_hours - 4.5, twiend_hours + 3)
night_t = t - 1
ax1.set_title(night_t.strftime('%Y/%m/%d'))
ax1.set_xlabel('UT [hours]')
ax1.set_yticks([])

# Add points for seeing
ax2 = ax1.twinx()
ax2.set_ylabel("Seeing [arcsec]")
ax2.scatter(guidetime, guide['seeing'], c='gray') #, marker='o') 
y1, y2 = ax2.get_ylim()
ax2.set_ylim(0, y2) 

plt.savefig(outplot, bbox_inches="tight")
if args.verbose: 
    print("Wrote", outplot)
