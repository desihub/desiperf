'''
@author: Parker Fagrelius (pfagrelius@noao.edu)

start server with following commands:

bokeh serve --show instperfapp

view at http://localhost:5006/instperfapp

'''

from bokeh.io import curdoc
import bokeh.plotting as bk 
from bokeh.models import (LinearColorMapper, ColorBar, ColumnDataSource,
    Title, Button, CheckboxButtonGroup)
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models.widgets.markups import Div
from pages.focalplane import FocalPlanePage
from pages.positioner import PosAccPage
from pages.tput import TputPage
from pages.detector import DetectorPage
from pages.guiding import GuidingPage
from data_handler import DataHandler


title_1 = Div(text='''<font size="4">Instrument Peformance Tool</font>''', width=500)
init_bt = Button(label="Initialize Data", button_type='primary',width=300)

DH = DataHandler()
timestamp_source = DH.data_source
exp_source = DH.exp_source


FP = FocalPlanePage(timestamp_source)
PP = PosAccPage(timestamp_source)
TP = TputPage(timestamp_source)
DP = DetectorPage(exp_source)
GP = GuidingPage(timestamp_source)
for page in [FP, PP, TP, DP, GP]:
    page.run()


def update_data():
    print("Update Data function disabled currently")
    # DH.update_data()
    # updated_data = DH.data_source
    # FP.update_data(updated_data)


init_bt.on_click(update_data)

''' LAYOUTS '''

layout1 = layout([[title_1],
                 [init_bt]])
tab1 = Panel(child=layout1, title="Data Initilization")

tab2 = FP.page_layout()
tab3 = PP.page_layout()
tab4 = GP.page_layout()
tab5 = TP.page_layout()
tab6 = DP.page_layout()


tabs = Tabs(tabs=[tab1, tab2, tab3, tab4, tab5, tab6])

curdoc().title = 'DESI Instrument Performance Tool'
curdoc().add_root(tabs)
