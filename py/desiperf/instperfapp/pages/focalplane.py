
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
from static.attributes import Focalplane_attributes
from scipy import stats


class FocalPlanePage(Plots):
    def __init__(self, datahandler):
        Plots.__init__(self,'Focal Plane', source=datahandler.focalplane_source)
        desc = """ These plots show the average behavior across the whole focal plate for a given time or exposure.
            """
        self.description = Div(text=desc, width=800, css_classes=['inst-style'])

        self.default_categories = list(Focalplane_attributes.keys())
        self.default_options = Focalplane_attributes



    def page_layout(self):
        this_layout = layout([[self.header],
                              [self.description],
                              [self.x_cat_select, self.y_cat_select],
                              [self.x_select, self.y_select, self.btn],

                              [self.obstype_option],
                              [self.attr_header],

                              [self.bin_option, self.bin_slider, self.save_btn],
                              [Div(text=" ",width=200), self.main_plot],
                              [self.desc_header],
                              [self.data_det_option, self.details],
                              [Div(text=" ",width=150), self.cov],

                              [self.plot_trend_option, self.mp_tl_det, self.ts1_tl_det, self.ts2_tl_det],
                              [self.details, self.cov],
                              [self.time_header],
                              [self.ts1],
                              [self.ts2]])
        tab = Panel(child=this_layout, title=self.title)
        return tab

    def run(self):
        #Layout
        self.x_options = self.default_options
        self.y_options = self.default_options
        self.x_cat_options = self.default_categories
        self.y_cat_options = self.default_categories
        self.prepare_layout_two_menus()

        #Get Data
        self.get_data('DATETIME',self.x_select.value, self.y_select.value, other_attr = ['EXPID','OBSTYPE','PROGRAM'])
        self.page_tooltips = [
            ("exposure","@EXPID"),
            ("obstime","@DATETIME{%F}"),
            ("obstype","@OBSTYPE"),
            ("program","@PROGRAM"),
            ("{}".format(self.x_select.value),"@attr1"),
            ("{}".format(self.y_select.value),"@attr2"),]

        #Plots
        self.time_series_plot()

        #Buttons and actions
        self.activate_buttons()
