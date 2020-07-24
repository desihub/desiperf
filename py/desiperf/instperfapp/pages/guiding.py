
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource, PreText, Select, Button
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
import pandas as pd 

from static.plots import Plots

class GuidingPage():
    def __init__(self, datahandler):
        self.plots = Plots('Guiding Performance',datahandler.focalplane_source)
        self.description = Div(text='These plots show the behavior of the GFA cameras during a given time or exposure.', width=800, style=self.plots.text_style)
        self.btn = Button(label='OK', button_type='primary', width=200)
        self.details = PreText(text=' ', width=500)
        self.data_source = self.plots.data_source
        self.default_options = ['targtra','targtdec', 'exptime', 'airmass', 'mountha', 'zd', 'mountaz',
       'domeaz', 'mjd_obs', 'date_obs', 'moonra',
       'moondec', 'EXPOSURE', 'max_blind', 'max_blind_95', 'rms_blind',
       'rms_blind_95', 'max_corr', 'max_corr_95', 'rms_corr',
       'rms_corr_95',  'mirror_avg_temp', 'mirror_desired_temp',
       'air_temp', 'air_dewpoint', 'air_flow',
       'probe1_humidity', 'probe1_temp', 'probe2_humidity', 'probe2_temp',
       'flowrate_in', 'flowrate_out', 'mirror_rtd_temp','glycol_in_temp', 'glycol_out_temp',
       'air_in_temp', 'air_out_temp', 'truss_ntt_temp', 'truss_ett_temp',
       'hinge_s_temp', 'hinge_w_temp', 'chimney_os_temp',
       'chimney_ow_temp', 'chimney_ib_temp', 'chimney_im_temp',
       'chimney_it_temp', 'centersection_i_temp', 'centersection_o_temp',
       'primarycell_i_temp', 'primarycell_o_temp', 'casscage_i_temp',
       'casscage_o_temp', 'decbore_temp', 'mirror_status',
       'row_status_user', 'mirror_temp', 'truss_temp', 'EXPID',
       'environmentmonitor_tower', 'tower_timestamp', 'wind_speed',
       'wind_direction', 'humidity', 'pressure', 'temperature',
       'dewpoint', 'split.1', 'gust', 'fvc_camerastatus',
       'controller_open', 'reset', 'initialized', 'shutter_open',
       'fan_on', 'temp_degc', 'exptime_sec', 'psf_pixels', 'last_updated',
       'guider_summary', 'duration', 'expid', 'seeing.1', 'frames.1',
       'meanx', 'meany', 'meanx2', 'meany2', 'meanxy', 'maxx', 'maxy',
       'guider_centroids', 'combined_x', 'combined_y']

        self.x_select = Select(title='Option 1', value='meanx',options=self.default_options)
        self.y_select = Select(title='Option 2', value='airmass', options=self.default_options)
        self.btn = Button(label='Plot', button_type='primary', width=200)

    def get_data(self, attr1, attr2, update=False):
        data = pd.DataFrame(self.data_source.data)[['mjd_obs',attr1,attr2]]
        self.details.text = str(data.describe())
        #self.cov.text = str(data.cov())
        data_ = data.rename(columns={attr1:'attr1',attr2:'attr2'}) 
        if update:
            self.plot_source.data = data_
        else:
            self.plot_source = ColumnDataSource(data_)
        self.time_series_plot()

    def page_layout(self):
        this_layout = layout([[self.plots.header],
                      [self.description],
                      [self.x_select, self.y_select, self.btn],
                      [self.corr,self.details],
                      [self.ts1],
                      [self.ts2]])
        tab = Panel(child=this_layout, title=self.plots.title)
        return tab

    def time_series_plot(self):
        self.corr = self.plots.figure(width=350, height=250, x_axis_label='attr1', y_axis_label='attr2')
        self.ts1 = self.plots.figure(x_axis_label='mjd_obs', y_axis_label='attr1')
        self.ts2 = self.plots.figure(x_axis_label='mjd_obs', y_axis_label='attr2')
        if self.data_source is not None:
            self.plots.corr_plot(self.corr, x='attr1',y='attr2', source=self.plot_source)
            self.plots.circle_plot(self.ts1, x='mjd_obs',y='attr1',source=self.plot_source)
            self.plots.circle_plot(self.ts2, x='mjd_obs',y='attr2',source=self.plot_source)
            #self.corr.circle(x='attr1', y='attr2', size=2, source=self.plot_source, selection_color="orange", alpha=0.6, nonselection_alpha=0.1, selection_alpha=0.4)
            #self.ts1.circle(x='mjd_obs', y='attr1', size=5, source=self.plot_source, color="blue", selection_color="orange")
            #self.ts2.circle(x='mjd_obs', y='attr2', size=5, source=self.plot_source, color="blue", selection_color="orange")


    def update(self):
        self.get_data(self.x_select.value, self.y_select.value, update=True)
        self.time_series_plot()

    def run(self):
        self.get_data(self.x_select.value, self.y_select.value)
        self.time_series_plot()
        self.btn.on_click(self.update)
