
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel
from bokeh.models import ColumnDataSource, Select
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select
from bokeh.plotting import figure
import pandas as pd

from static.plots import Plots


class FocalPlanePage():
    def __init__(self, datahandler):
        self.plots = Plots('Focal Plane Performance', datahandler.focalplane_source)
        self.details = PreText(text=' ', width=500)
        self.cov = PreText(text=' ', width=500)
        self.data_source = self.plots.data_source
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

        self.x_select = Select(value='max_blind', options=self.default_options)
        self.y_select = Select(value='airmass', options=self.default_options)
        self.btn = Button(label='Plot', button_type='primary', width=200)

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
        this_layout = layout([[self.plots.header],
                              [self.x_select, self.y_select, self.btn],
                              [self.corr, self.details, self.cov],
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
