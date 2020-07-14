
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel
from bokeh.models import ColumnDataSource, Select
from bokeh.plotting import figure
import pandas as pd

from static.page import Page


class FocalPlanePage(Page):
    def __init__(self, source=None):
        self.page = Page('Focal Plane Performance', source)
        self.details = self.page.pretext(' ')
        self.cov = self.page.pretext(' ')
        self.data_source = self.page.data_source
        self.default_options = ['skyra', 'skydec',  'exptime', 'tileid',
                                'reqra', 'reqdec', 'targtra', 'targtdec',
                                'zenith', 'mjd_obs', 'moonra', 'moondec',
                                'EXPOSURE', 'max_blind', 'max_blind_95',
                                'rms_blind', 'rms_blind_95', 'max_corr',
                                'max_corr_95', 'rms_corr', 'rms_corr_95',
                                'mirror_temp', 'truss_temp', 'air_temp',
                                'mirror_avg_temp', 'wind_speed',
                                'wind_direction', 'humidity', 'pressure',
                                'dewpoint', 'shutter_open', 'exptime_sec',
                                'psf_pixels', 'hex_trim', 'hex_rot_rate',
                                'hex_status', 'hex_rot_offset',
                                'hex_rot_enabled', 'hex_position',
                                'hex_rot_interval', 'hex_tweak', 'adc_status',
                                'adc_home1', 'adc_home2', 'adc_nrev1',
                                'adc_nrev2', 'adc_angle1', 'adc_angle2',
                                'adc_status', 'adc_status1', 'adc_status2',
                                'adc_rem_time1', 'adc_rem_time2']

        self.x_select = self.page.select('max_blind', self.default_options)
        self.y_select = self.page.select('airmass', self.default_options)
        self.btn = self.page.button('Plot')

    def get_data(self, attr1, attr2, update=False):
        data = pd.DataFrame(self.data_source.data)[['mjd_obs', attr1, attr2]]
        self.details.text = str(data.describe())
        self.cov.text = str(data.cov())
        data_ = data.rename(columns={attr1:'attr1', attr2:'attr2'}) 
        if update:
            self.plot_source.data = data_
        else:
            self.plot_source = ColumnDataSource(data_)

    def page_layout(self):
        this_layout = layout([[self.page.header],
                              [self.x_select, self.y_select, self.btn],
                              [self.corr, self.details, self.cov],
                              [self.ts1],
                              [self.ts2]])
        tab = Panel(child=this_layout, title=self.page.title)
        return tab

    def time_series_plot(self):
        self.corr = figure(plot_width=350, plot_height=250, tools=self.page.tools, x_axis_label=self.x_select.value, y_axis_label=self.y_select.value)
        self.ts1 = figure(plot_width=900, plot_height=200, tools=self.page.tools, x_axis_label='MJD_OBS', y_axis_label=self.x_select.value)
        self.ts2 = figure(plot_width=900, plot_height=200, tools=self.page.tools, x_axis_label='MJD_OBS', y_axis_label=self.y_select.value)
        if self.data_source is not None:
            self.corr.circle(x='attr1', y='attr2', size=2, source=self.plot_source, selection_color="orange", alpha=0.6, nonselection_alpha=0.1, selection_alpha=0.4)
            self.ts1.circle(x='mjd_obs', y='attr1', size=5, source=self.plot_source, color="blue", selection_color="orange")
            self.ts2.circle(x='mjd_obs', y='attr2', size=5, source=self.plot_source, color="blue", selection_color="orange")

    def update(self):
        self.get_data(self.x_select.value, self.y_select.value, update=True)
        self.time_series_plot()

    def run(self):
        self.get_data(self.x_select.value, self.y_select.value)
        self.time_series_plot()
        self.btn.on_click(self.update)
