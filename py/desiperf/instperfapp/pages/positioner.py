
import os
import glob
import pandas as pd
import numpy as np

from bokeh.layouts import column, layout, row
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select, CustomJS, TextInput, RadioGroup
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure

from static.attributes import Positioner_attributes
from static.page import Page
from static.plots import Plots

class PosAccPage(Page):
    def __init__(self, datahandler):
        Page.__init__(self,'Positioner',source=None)
        self.page_name = 'pos'
        self.DH = datahandler

        desc = """These plots show behavior for a single (selected) positioner over time.
        Press Re-Plot button when change attribute, positioner selection, binning, or obstype.
            """
        self.description = Div(text=desc, width=800, css_classes=['inst-style'])

        self.default_categories = list(Positioner_attributes.keys())
        self.default_options = Positioner_attributes

        self.pos = str(6830)

        self.select_header = Div(text="Select Positioner(s) to Plot", width=1000, css_classes=['subt-style'])
        self.enter_pos_option = RadioGroup(labels=["Enter POS ID","OR Select from lists"], active=0)
        self.pos_enter = TextInput(title="POS",value=self.pos)
        self.pos_select = Select(title='Select POS', value='ALL')
        self.can_select = Select(title='Select CAN', value='ALL', options=['ALL','10','11','12','13','14','15','16','17','20','21'])
        self.petal_select = Select(title='Select PETAL', value='ALL', options=['ALL','0','1','2','3','4','5','6','7','8','9'])

        self.fp = self.DH.fiberpos

    def page_layout(self):
        this_layout = layout([[self.header],
                        [self.description],
                        [self.x_cat_select, self.y_cat_select],
                        [self.x_select, self.y_select, self.btn],

                        [self.line],
                        [self.select_header], 
                        [column([Div(text=' ',height=50), self.pos_enter, self.enter_pos_option, self.petal_select, self.can_select, self.pos_select]), self.scatt],
                        [self.attr_header],

                        [self.line],
                        [self.bin_option, self.bin_slider, self.save_btn],
                        [Div(text=' ',height=200),self.ts0,[self.plot_trend_option, self.mp_tl_det]],

                        [self.line],
                        [self.desc_header],
                        [self.data_det_option, self.details],

                        [self.line],
                        [self.time_header],
                        [self.ts1, self.ts1_tl_det],
                        [self.ts2, self.ts2_tl_det]])
        tab = Panel(child=this_layout, title=self.title)
        return tab

    def pos_selection(self, attr, old, new):
        self.petal = self.petal_select.value
        self.can = self.can_select.value

        if (self.petal == 'ALL') & (self.can == 'ALL'):
            pos_list = []
        elif (self.petal == 'ALL') & (self.can != 'ALL'):
            pos_list = list(self.fp[(self.fp.BUS_ID == int(self.can))].CAN_ID)
        elif (self.petal != 'ALL') & (self.can == 'ALL'):
            pos_list = list(self.fp[(self.fp.PETAL == int(self.petal))].CAN_ID)
        else:
            pos_list = list(self.fp[(self.fp.PETAL == int(self.petal))&(self.fp.BUS_ID == int(self.can))].CAN_ID)
        
        self.pos_select.options = ['ALL'] + [str(p) for p in pos_list]

    def get_selection(self):
        if self.enter_pos_option.active == 0:
            self.pos = self.pos_enter.value
            self.can = int(np.unique(self.fp[self.fp.CAN_ID == int(self.pos)].BUS_ID)[0])
            self.petal = int(np.unique(self.fp[self.fp.CAN_ID == int(self.pos)].PETAL)[0])
        else:
            self.pos = self.pos_select.value
            self.can = self.can_select.value
            self.petal = self.petal_select.value

        if self.pos != 'ALL':
            self.pos_files = [os.path.join(self.DH.pos_dir, '{}.csv'.format(self.pos))]
            row = self.fp[self.fp.CAN_ID == int(self.pos)]
            self.index = row.index

        elif self.petal != 'ALL':
            if self.can == 'ALL':
                pos = self.fp[self.fp.PETAL == int(self.petal)]
                self.index = pos.index
                self.pos_files = [os.path.join(self.DH.pos_dir, '{}.csv'.format(p)) for p in pos.CAN_ID]
            else:
                pos = self.fp[(self.fp.PETAL == int(self.petal))&(self.fp.BUS_ID == int(self.can))]
                self.pos_files = [os.path.join(self.DH.pos_dir, '{}.csv'.format(p)) for p in pos.CAN_ID]
                self.index = pos.index
        elif self.can != 'ALL':
            if self.petal == 'ALL':
                pos = self.fp[(self.fp.BUS_ID == int(self.can))]
                self.pos_files = [os.path.join(self.DH.pos_dir, '{}.csv'.format(p)) for p in pos.CAN_ID]
                self.index = pos.index


    def run(self):
        #Layout
        self.x_options = self.default_options
        self.y_options = self.default_options
        self.x_cat_options = self.default_categories
        self.y_cat_options = self.default_categories
        self.prepare_layout()

        #Get data
        self.get_selection()
        self.get_data('DATETIME',self.x_select.value, self.y_select.value, other_attr=['EXPID','OBSTYPE','PROGRAM','DEVICE_LOC','PETAL_LOC','SPECTRO'])

        self.page_tooltips = [
            ("exposure","@EXPID"),
            ("obstime","@DATETIME{%F}"),
            ("obstype","@OBSTYPE"),
            ("program","@PROGRAM"),
            ("dev","@DEVICE_LOC"),
            ("petal","@PETAL_LOC"),
            ("spectro","@SPECTRO"),
            ("x attr.","@attr1"),
            ("y attr.","@attr2"),]

        self.pos_tooltips = [
            ("Petal","@PETAL"),
            ("POS ID","@CAN_ID"),
            ("CAN","@BUS_ID"),
            ("DEV LOC","@DEVICE"),
            ("FIBER No.","@FIBER"),
            ("(x,y,z)","(@X,@Y,@Z)")]
        #            ("POS ID","@CAN_ID"),
        #Plots
        self.time_series_plot()
        self.pos_loc_plot()

        #Buttons and actions
        self.activate_buttons()
        self.petal_select.on_change('value',self.pos_selection)
        self.can_select.on_change('value',self.pos_selection)
        