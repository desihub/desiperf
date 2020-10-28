
from bokeh.layouts import column, layout, row, gridplot
from bokeh.models.widgets import Panel
from bokeh.models import CustomJS, ColumnDataSource, Select, Slider, CheckboxGroup
from bokeh.models import Button, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
import pandas as pd
import numpy as np 
from datetime import datetime

from static.plots import Plots
from static.page import Page
from static.attributes import Focalplane_attributes
from scipy import stats


class FocalPlanePage(Page):
    def __init__(self, datahandler):
        Page.__init__(self,'Focal Plane', source=datahandler.focalplane_source)
        self.page_name = 'fp'
        desc = """ These plots show the average behavior across the whole focal plate for a given time or exposure. 
            Press Re-Plot button when change attribute, binning, or obstype.
            """
        self.description = Div(text=desc, width=800, css_classes=['inst-style'])

        self.default_categories = list(Focalplane_attributes.keys())
        self.default_options = Focalplane_attributes



    def page_layout(self):
        this_layout = layout([[self.header],
                              [self.description],
                              [self.x_cat_select, self.y_cat_select],
                              [self.x_select, self.y_select, self.btn],
                              [self.obstype_hdr, self.obstype_option],

                              [self.line],
                              [self.attr_header],
                              [self.bin_option, self.bin_slider, self.save_btn],
                              [self.ts0, [self.plot_trend_option, self.mp_tl_det]],

                              [self.line],
                              [self.desc_header],
                              [self.data_det_option, self.details],
                              [Div(text=" ",width=150), self.cov],

                              [self.line],
                              [self.time_header],
                              [self.ts1, self.ts1_tl_det],
                              [self.ts2, self.ts2_tl_det]])
        tab = Panel(child=this_layout, title=self.title)
        return tab

    def run(self):
        #Layout
        self.x_options = self.default_options
        self.y_options = self.default_options
        self.x_cat_options = self.default_categories
        self.y_cat_options = self.default_categories
        self.prepare_layout()

        #Get Data
        self.get_data('DATETIME',self.x_select.value, self.y_select.value, other_attr = ['EXPID','OBSTYPE','PROGRAM'])
        self.page_tooltips = [
            ("exposure","@EXPID"),
            ("obstime","@DATETIME{%F}"),
            ("obstype","@OBSTYPE"),
            ("program","@PROGRAM"),
            ("x attr.","@attr1"),
            ("y attr.","@attr2"),]

        #Plots
        self.time_series_plot()

        #Buttons and actions
        self.activate_buttons()
