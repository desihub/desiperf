
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel
from bokeh.models import CustomJS, ColumnDataSource, Select, Slider, CheckboxGroup
from bokeh.models import Button, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
import pandas as pd
import numpy as np 
from datetime import datetime

from static.plots import Plots
from scipy import stats


class FocalPlanePage(Plots):
    def __init__(self, datahandler):
        Plots.__init__(self,'Focal Plane Performance', source=datahandler.focalplane_source)
        self.description = Div(text='These plots show the average behavior across the whole focal plate for a given time or exposure.', 
                                width=800, style=self.text_style)

        self.default_options = ['datetime','EXPOSURE', 'max_blind', 'max_blind_95', 'rms_blind',
                                'rms_blind_95', 'max_corr', 'max_corr_95', 'rms_corr','rms_corr_95',
                                'targtra','targtdec', 'exptime', 'airmass', 'mountha', 'mountaz',
                                'domeaz',  'moonra','moondec',   'mirror_avg_temp', 
                                'air_temp', 'air_dewpoint', 'air_flow', 'mirror_temp', 'truss_temp', 'wind_speed',
                                'wind_direction', 'humidity', 'pressure', 'temperature','dewpoint',  'gust', 'fan_on', 
                                'temp_degc', 'exptime_sec', 'psf_pixels', 'seeing.1']


    def page_layout(self):
        this_layout = layout([[self.header],
                              [self.description],
                              [self.x_select, self.y_select, self.btn],
                              [self.bin_option, self.save_btn],
                              [self.bin_slider, self.replot_btn],
                              [self.corr, self.details, self.cov],
                              [self.ts1],
                              [self.ts2]])
        tab = Panel(child=this_layout, title=self.title)
        return tab

    def run(self):
        self.x_options = self.default_options
        self.y_options = self.default_options
        self.prepare_layout()
        self.x_select.value = 'max_blind'
        self.y_select.value = 'airmass'
        self.get_data('datetime',self.x_select.value, self.y_select.value, other_attr = ['EXPOSURE'])
        self.page_tooltips = [
            ("exposure","@EXPOSURE"),
            ("{}".format(self.x_select.value),"@attr1"),
            ("{}".format(self.y_select.value),"@attr2"),
            ("(x,y)", "($x, $y)")]
        self.time_series_plot()
        self.bin_plot('new',[0],[0])
        self.btn.on_click(self.update)
        self.replot_btn.on_click(self.update_binned_data)
        self.bin_option.on_change('active',self.bin_plot)
        self.save_btn.on_click(self.save_data)
        self.plot_source.selected.js_on_change('indices', CustomJS(args=dict(s1=self.plot_source, s2=self.sel_data), code="""
                                                var inds = cb_obj.indices;
                                                var d1 = s1.data;
                                                var d2 = s2.data;
                                                d2['attr1'] = []
                                                d2['attr2'] = []
                                                for (var i = 0; i < inds.length; i++) {
                                                    d2['attr1'].push(d1['attr1'][inds[i]])
                                                    d2['attr2'].push(d1['attr2'][inds[i]])
                                                }
                                                s2.change.emit();
                                                s2.data = d2 """))
