'''
@author: Parker Fagrelius (pfagrelius@noao.edu)

start server with following commands:

bokeh serve --show instperfapp

view at http://localhost:5006/instperfapp

'''
import pandas as pd

from bokeh.io import curdoc
from bokeh.models import Button, TextInput, PreText
from bokeh.layouts import layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models.widgets.markups import Div

from pages.focalplane import FocalPlanePage
from pages.positioner import PosAccPage
from pages.tput import TputPage
from pages.detector import DetectorPage
from pages.guiding import GuidingPage
from bokeh.models.callbacks import CustomJS

from data_mgt.data_handler import DataHandler


title_1 = Div(text="Instrument Peformance Tool", width=500, style={'font-family':'serif', 'font-size':'250%'})

#- Initialize data
DH = DataHandler()
DH.run()

#- Popup (doesn't work yet)
#callback_holder = PreText(text='', css_classes=['hidden'], visible=False)
#callback = CustomJS(args={}, code='alert(cb_obj.text);')

def init_pages(datahandler):
    '''
    Args:
        DH : DataHandler; points to which data to use in creating pages/plots

    Calls the individual pages and initializes the data used
    '''
    FP = FocalPlanePage(datahandler)
    PP = PosAccPage(datahandler) #Has its own data
    TP = TputPage(datahandler)#Data not available yet
    DP = DetectorPage(datahandler)
    GP = GuidingPage(datahandler)
    for page in [FP, PP, TP, DP, GP]:
        page.run()

    return FP.page_layout(), PP.page_layout(), GP.page_layout(), TP.page_layout(), DP.page_layout()

# def update_data():
#     print("You must run this on the desi server")
#     #callback_holder.js_on_change('text', callback)
#     #callback_holder.text = "Are you sure!"

#     DH = DataHandler(option='init')
#     DH.run()
#     connect_info.text = DH.DS.connect_info
#     fp_tab, pp_tab, gp_tab, tp_tab, dp_tab = init_pages(DH)
#     tab2.children = fp_tab
#     tab3.children = pp_tab
#     tab4.children = gp_tab
#     tab5.children = tp_tab
#     tab6.children = dp_tab

#- Page Logo
page_logo = Div(text="<img src='instperfapp/static/logo.png'>", width=350, height=300)

#- Landing page widgets
ds = pd.DataFrame(DH.detector_source.data)
fps = pd.DataFrame(DH.focalplane_source.data)
data_info = PreText(text="Data is available for the dates listed below.\n Detector Data: {} - {} (Exposures {} - {}) \n Focalplane Data: {} - {} (Exposures {} - {})".format(int(min(ds.NIGHT)), int(max(ds.NIGHT)), int(min(ds.EXPID)), int(max(ds.EXPID)), int(min(fps.night)), int(max(fps.night)), int(min(fps.EXPID)), int(max(fps.EXPID))),width=800,style={'font-family':'serif', 'font-size':'150%'})

#start_date = TextInput(title='Start Date', value=DH.start_date)
#end_date = TextInput(title='End Date', value=DH.start_date)
#init_bt = Button(label="Initialize Data", button_type='primary', width=300)
connect_info = Div(text=DH.DS.connect_info, width=300)

fp_tab, pp_tab, gp_tab, tp_tab, dp_tab = init_pages(DH)
#init_bt.on_click(update_data)

#- Popup 


''' LAYOUTS '''

layout1 = layout([[title_1],
                  [page_logo],
                  [data_info],
                  [connect_info]])
tab1 = Panel(child=layout1, title="Data Initialization")

tab2 = fp_tab
tab3 = pp_tab
tab4 = gp_tab
tab5 = tp_tab
tab6 = dp_tab

tabs = Tabs(tabs=[tab1, tab2, tab3, tab4, tab5, tab6])

curdoc().title = 'DESI Instrument Performance Tool'
curdoc().add_root(tabs)
