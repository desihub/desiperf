
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource, PreText, Select, Button, CustomJS
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
import pandas as pd 

from static.plots import Plots

class GuidingPage(Plots):
    def __init__(self, datahandler):
        Plots.__init__(self,'Guiding Performance',datahandler.focalplane_source)
        self.description = Div(text='These plots show the behavior of the GFA cameras during a given time or exposure.', 
                                width=800, style=self.text_style)

        self.default_options = ['datetime','EXPOSURE','meanx', 'meany', 'meanx2', 'meany2', 'meanxy', 'maxx', 'maxy',
                                'guider_centroids', 'combined_x', 'combined_y', 'airmass', 'domeaz', 'moonra','moondec', 
                                'air_temp',  'mirror_temp', 'wind_speed','wind_direction', 'humidity', 'pressure', 'temperature',
                                'dewpoint', 'fan_on', 'temp_degc', 'exptime_sec', 'psf_pixels', 'guider_summary', 'duration','seeing.1', ]


    def page_layout(self):
        this_layout = layout([[self.header],
                      [self.description],
                      [self.x_select, self.y_select, self.btn],
                      [self.bin_option, self.save_btn],
                      [self.bin_slider, self.replot_btn, self.data_det_option],
                      [self.corr,self.details],
                      [self.ts1],
                      [self.ts2]])
        tab = Panel(child=this_layout, title=self.title)
        return tab


    def run(self):
        self.x_options = self.default_options
        self.y_options = self.default_options
        self.prepare_layout()
        self.x_select.value = 'meanx'
        self.y_select.value = 'airmass'
        self.get_data('datetime',self.x_select.value, self.y_select.value, other_attr=['EXPOSURE'])
        self.page_tooltips = [
            ("exposure","@EXPOSURE"),
            ("{}".format(self.x_select.value),"@attr1"),
            ("{}".format(self.y_select.value),"@attr2"),
            ("(x,y)", "($x, $y)")]
        self.time_series_plot()
        self.bin_plot('new',[0],[0])
        self.btn.on_click(self.update)
        self.replot_btn.on_click(self.plot_binned_data)
        self.bin_option.on_change('active',self.bin_plot)
        self.save_btn.on_click(self.save_data)
        self.data_det_option.on_change('active', self.data_det_type)
        self.plot_source.selected.on_change('indices', self.update_selected_data)

