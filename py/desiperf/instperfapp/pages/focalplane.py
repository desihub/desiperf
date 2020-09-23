
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
        self.description = Div(text=desc, width=800, style=self.text_style)

        self.default_categories = list(Focalplane_attributes.keys())
        self.default_options = Focalplane_attributes

    def page_layout(self):
        this_layout = layout([[self.header],
                              [self.description],
                              [self.x_cat_select, self.y_cat_select],
                              [self.x_select, self.y_select, self.btn],
                              [[self.main_plot], column([self.data_det_option, self.save_btn, self.bin_slider, self.bin_option, self.replot_btn]),[self.obstype_option]],
                              [self.details, self.cov],
                              [self.ts1],
                              [self.ts2]])
        tab = Panel(child=this_layout, title=self.title)
        return tab

    def run(self):
        self.x_options = self.default_options
        self.y_options = self.default_options
        self.x_cat_options = self.default_categories
        self.y_cat_options = self.default_categories
        self.prepare_layout_two_menus()
        self.x_cat_select.value = self.default_categories[0]
        self.y_cat_select.value = self.default_categories[1]
        self.x_select.value = self.default_options[self.default_categories[0]][0]
        self.y_select.value = self.default_options[self.default_categories[1]][0]
        self.get_data('datetime',self.x_select.value, self.y_select.value, other_attr = ['EXPID'])
        self.page_tooltips = [
            ("exposure","@EXPID"),
            ("{}".format(self.x_select.value),"@attr1"),
            ("{}".format(self.y_select.value),"@attr2"),
            ("(x,y)", "($x, $y)")]
        self.time_series_plot()
        self.bin_plot('new',[0],[0])
        self.btn.on_click(self.update)
        self.replot_btn.on_click(self.plot_binned_data)
        self.bin_option.on_change('active',self.bin_plot)
        self.obstype_option.on_change('active',self.obstype_selection)
        self.save_btn.on_click(self.save_data)
        self.data_det_option.on_change('active',self.data_det_type)
        self.plot_source.selected.on_change('indices', self.update_selected_data)
