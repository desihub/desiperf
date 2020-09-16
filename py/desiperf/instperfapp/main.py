'''
@author: Parker Fagrelius (pfagrelius@noao.edu)

start server with following commands:

bokeh serve --show instperfapp

view at http://localhost:5006/instperfapp

'''
import pandas as pd

from bokeh.io import curdoc
from bokeh.models import Button, TextInput, PreText, ColumnDataSource
from bokeh.models.widgets.tables import DataTable, TableColumn
from bokeh.layouts import layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models.widgets.markups import Div

from pages.focalplane import FocalPlanePage
from pages.positioner import PosAccPage
from pages.spectrograph import SpectrographPage
from bokeh.models.callbacks import CustomJS

from data_mgt.data_handler import DataHandler


def init_pages(datahandler):
    '''
    Args:
        DH : DataHandler; points to which data to use in creating pages/plots

    Calls the individual pages and initializes the data used
    '''
    FP = FocalPlanePage(datahandler)
    PP = PosAccPage(datahandler) #Has its own data
    SP = SpectrographPage(datahandler)
    for page in [FP, PP, SP]:
        page.run()

    return FP.page_layout(), PP.page_layout(), SP.page_layout()

def update_data():
    print('Updating data')
    date_btn.label = 'Updating'
    DH = DataHandler(start_date=str(start_date.value), end_date=str(end_date.value), option='no_update')
    DH.run()
    fp_tab, pp_tab, sp_tab = init_pages(DH)
    ds = pd.DataFrame(DH.detector_source.data)
    fps = pd.DataFrame(DH.focalplane_source.data)
    data_source.data = data_text(ds, fps)
    start_date.value = None
    end_date.value = None
    date_btn.label = 'Updated' 

def data_text(ds, fps):
    sp = ['Spectrograph Data', int(min(ds.NIGHT)), int(max(ds.NIGHT)), int(min(ds.EXPID)), int(max(ds.EXPID))]
    fp = ['FocalPlane Data', int(min(fps.night)), int(max(fps.night)), int(min(fps.EXPID)), int(max(fps.EXPID))]
    df = pd.DataFrame([sp,fp], columns = ['type','date_start','date_end','exp_start','exp_end'])
    return df


#- Initialize data & pages
DH = DataHandler()
DH.run()
fp_tab, pp_tab, sp_tab = init_pages(DH)

#- Welcome Page
title_1 = Div(text="DESI Instrument Peformance Analysis Tool", width=800, css_classes=['h1-title-style'])
page_logo = Div(text="<img src='instperfapp/static/logo.png'>", width=350, height=300)

welcome_text = """ Welcome to the DESI Instrument Performance Analysis Tool!
                This tool uses data from a variety of sources (see below) to help us evaluate the performance of the 
                instrument over timeand identify potential improvements. This tool provides data for the analysis of 
                DESI performance during an exposure, whichincludes fiber positioning, guiding, spectrograph throughput, and detector noise."""

welcome = Div(text=welcome_text, width=800, css_classes=['inst-style'])

subtitle1 = Div(text="Data Overview", width=800, css_classes=['title-style'])
ds = pd.DataFrame(DH.detector_source.data)
fps = pd.DataFrame(DH.focalplane_source.data)
df = data_text(ds, fps)
data_source = ColumnDataSource(df)

columns = [TableColumn(field='type', title='Data Source', width=200),
           TableColumn(field='date_start', title='Date Start', width=100),
           TableColumn(field='date_end', title='Date End', width=100),
           TableColumn(field='exp_start', title='Exposure Start', width=100),
           TableColumn(field='exp_end', title='Exposure End', width=100)]

data_table = DataTable(source=data_source, columns=columns, height=100)


subtitle1_5 = Div(text="<b>Limit the data to a shorter date range below.</b>", width=800, css_classes=['inst-style'])
start_date = TextInput(title ='Start Date', width=200, placeholder = str(int(min(ds.NIGHT))))
end_date = TextInput(title ='End Date', width=200, placeholder = str(int(max(ds.NIGHT))))
data_update_info = Div(text=' ', width=800, css_classes=['alert-style'])
date_btn = Button(label='Update Date Range', width=200, css_classes=['connect_button'])


data_instructions = Div(text='To expand the date range up to the current date, run <b>data_script.py</b> on the desi server. [This is only for the time being]', width=800, css_classes=['inst-style'])

subtitle2 = Div(text="Page Descriptions: ", width=800, css_classes=['title-style'])
page_desc = """<b>FocalPlane:</b> This page provides data to analyze the performance of the focalplane, specifically: overall mean 
            positioner, guiding, GFA, FVC, and Corrector performance. These can be analyzed as a function of time or 
            against other observation and telescope telemetry.
            <b>Positioner:</b> This page provides the performance data for individual positioners, CAN buses, and petals. 
            This performance can be analyzed as a function of time or against guiding, GFA, FVC performance and observation/telescope telemetry.
            <b>Spectrograph:</b> This page provides data to analyze the performance of the spectrographs, specifically the 
            detectors in each spectrograph. This can be analzyed as a function of time or against observation/telescope 
            telemetry, spectrograph and shack telemetry.
            """
page_info = Div(text=page_desc, width=800, css_classes=['inst-style'])

contact_desc = """
               If you have any issues with the code, please log it on github: https://github.com/desihub/desiper
               Please contact pfagrelius-at-noao-dot-edu or martini-dot-10-at-osu-dot-edu with questions or issues
               """
contact_info = Div(text=contact_desc, width=800, css_classes=['inst-style'])

#- LAYOUTS 
layout1 = layout([[title_1],
                  [page_logo],
                  [welcome],
                  [subtitle1],
                  [data_table],
                  [subtitle1_5],
                  [start_date, end_date, date_btn],
                  [data_update_info],
                  [data_instructions],
                  [subtitle2],
                  [page_info],
                  [contact_info]])
tab1 = Panel(child=layout1, title="Welcome")

tab2 = fp_tab
tab3 = pp_tab
tab4 = sp_tab

tabs = Tabs(tabs=[tab1, tab2, tab3, tab4])

date_btn.on_click(update_data)

curdoc().title = 'DESI Instrument Performance Analysis Tool'
curdoc().add_root(tabs)
