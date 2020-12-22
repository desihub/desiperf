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
elif os.path.isdir(coriroot): 
    nightdir = os.path.join(coriroot, night) 
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
        
# Compute total science and guiding time 

# in hours
twibeg_hours = 24.*(twibeg.mjd - startdate)
twiend_hours = 24.*(twiend.mjd - startdate)
total_hours = twiend_hours - twibeg_hours 

# as a percent of dark time
guiding_percent = 100.*np.sum(guide_width)/total_hours
science_percent = 100.*np.sum(science_width)/total_hours

plt.figure(figsize=(14,4))
barheight = 0.25

y_arc = 0
y_flat = 1
y_guide = 2
y_science = 3

ymin = -1
ymax = 4

# Draw time sequence for spectroscopy, guiding, flats, and arcs -- 

plt.barh(y_science, science_width, 2*barheight, science_start, align='center', color='b')
plt.barh(y_science, dither_width, 2*barheight, dither_start, align='center', color='c')
plt.barh(y_guide, guide_width, barheight, guide_start, align='center', color='b')
plt.barh(y_flat, flat_width, barheight, flat_start, align='center', color='k')
plt.barh(y_arc, arc_width, barheight, arc_start, align='center', color='r')

# Twilight

plt.plot([twibeg_hours, twibeg_hours], [ymin, ymax], 'k:')
plt.plot([twiend_hours, twiend_hours], [ymin, ymax], 'k:')

# Default label locations
xlab1 = float(twibeg_hours - 3.5)
xlab2 = float(twiend_hours + 0.5)

# Populate in case no data were obtained in each category
if len(science_start) == 0: 
    science_start.append(xlab1 + 4.)
    science_width.append(0.) 

if len(guide_start) == 0: 
    guide_start.append(xlab1 + 4.)
    guide_width.append(0.)

if len(flat_start) == 0: 
    flat_start.append(xlab2)
    flat_width.append(0.)
if len(arc_start) == 0: 
    arc_start.append(xlab2)
    arc_width.append(0.)

plt.text(xlab1, y_science, "Science", va='center')
plt.text(xlab1, y_guide, "Guiding", va='center')

# Adjust locations of science and guiding percentages -- 
sxlab = max(xlab2, science_start[-1] + science_width[-1] + 0.5) 
gxlab = max(xlab2, guide_start[-1] + guide_width[-1] + 0.5) 
slab = "{0:.1f}%".format(science_percent)
glab = "{0:.1f}%".format(guiding_percent)
plt.text(sxlab, y_science, slab, va='center')
plt.text(gxlab, y_guide, glab, va='center')

plt.text(xlab1, y_flat, "Flats", va='center')
plt.text(xlab1, y_arc, "Arcs", va='center')

# Adjust locations of Flats and Arcs labels 
#if flat_start[-1] >= xlab1 + 0.5:
#    plt.text(flat_start[-1] + 0.5, y_flat, "Flats", va='center')
#else: 
#    plt.text(xlab1, y_flat, "Flats", va='center')
##
#if arc_start[-1] >= xlab1 + 0.5:
#    plt.text(arc_start[-1]+0.5, y_arc, "Arcs", va='center')
#else: 
#    plt.text(xlab1, y_arc, "Arcs", va='center')

plt.ylim(ymin, ymax)   
plt.xlim(twibeg_hours - 4, twiend_hours + 3)

night_t = t - 1
plt.title(night_t.strftime('%Y/%m/%d'))
plt.xlabel('UT [hours]')

plt.savefig(outplot, bbox_inches="tight")
if args.verbose: 
    print("Wrote", outplot)
