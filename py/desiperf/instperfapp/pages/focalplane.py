
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel
from bokeh.models import CustomJS, ColumnDataSource, Select
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
import pandas as pd

from static.plots import Plots


class FocalPlanePage():
    def __init__(self, datahandler):
        self.plots = Plots('Focal Plane Performance', datahandler.focalplane_source)
        self.description = Div(text='These plots show the average behavior across the whole focal plate for a given time or exposure.', 
                                width=800, style=self.plots.text_style)
        self.details = PreText(text=' ', width=500)
        self.cov = PreText(text=' ', width=500)
        self.data_source = self.plots.data_source
        self.default_options = ['datetime','EXPOSURE', 'max_blind', 'max_blind_95', 'rms_blind',
                                'rms_blind_95', 'max_corr', 'max_corr_95', 'rms_corr','rms_corr_95',
                                'targtra','targtdec', 'exptime', 'airmass', 'mountha', 'mountaz',
                                'domeaz',  'moonra','moondec',   'mirror_avg_temp', 
                                'air_temp', 'air_dewpoint', 'air_flow', 'mirror_temp', 'truss_temp', 'wind_speed',
                                'wind_direction', 'humidity', 'pressure', 'temperature','dewpoint',  'gust', 'fan_on', 
                                'temp_degc', 'exptime_sec', 'psf_pixels', 'seeing.1']

        self.x_select = Select(title='Option 1', value='max_blind', options=self.default_options)
        self.y_select = Select(title='Option 2', value='airmass', options=self.default_options)
        self.btn = Button(label='Plot', button_type='primary', width=200)
        self.fp_tooltips = None

    def get_data(self, attr1, attr2, update=False):
        
        data = pd.DataFrame(self.data_source.data)[['datetime',attr1,attr2,'EXPOSURE']]
        self.dd = ColumnDataSource(data[['datetime', attr1, attr2]])
        self.details.text = 'Data Overview: \n ' + str(pd.DataFrame(self.dd.data).describe())
        self.cov.text = 'Covariance of Option 1 & 2: \n' + str(pd.DataFrame(self.dd.data).cov())
        data_ = data.rename(columns={attr1:'attr1', attr2:'attr2'}) 
        if update:
            self.plot_source.data = data_
            self.corr.xaxis.axis_label = attr1
            self.corr.yaxis.axis_label = attr2
            self.ts1.yaxis.axis_label = attr1
            self.ts2.yaxis.axis_label = attr2
            self.corr.title.text  = '{} vs {}'.format(attr1, attr2)
            self.ts1.title.text = 'Time vs. {}'.format(attr1)
            self.ts2.title.text = 'Time vs. {}'.format(attr2)
        else:
            self.plot_source = ColumnDataSource(data_)

        self.fp_tooltips = [
            ("exposure","@EXPOSURE"),
            ("{}".format(attr1),"@attr1"),
            ("{}".format(attr2),"@attr2"),
            ("(x,y)", "($x, $y)")]

    def page_layout(self):
        this_layout = layout([[self.plots.header],
                              [self.description],
                              [self.x_select, self.y_select, self.btn],
                              [self.corr, self.details, self.cov],
                              [self.ts1],
                              [self.ts2]])
        tab = Panel(child=this_layout, title=self.plots.title)
        return tab

    def time_series_plot(self):
        self.corr = self.plots.figure(width=450, height=450, tooltips=self.fp_tooltips, x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, title='{} vs {}'.format(self.x_select.value, self.y_select.value))
        self.ts1 = self.plots.figure(x_axis_label='datetime', tooltips=self.fp_tooltips, y_axis_label=self.x_select.value, title='Time vs. {}'.format(self.x_select.value))
        self.ts2 = self.plots.figure(x_axis_label='datetime', tooltips=self.fp_tooltips, y_axis_label=self.y_select.value, title='Time vs. {}'.format(self.y_select.value))
        if self.data_source is not None:
            self.plots.corr_plot(self.corr, x='attr1',y='attr2', source=self.plot_source)
            self.plots.circle_plot(self.ts1, x='datetime',y='attr1',source=self.plot_source)
            self.plots.circle_plot(self.ts2, x='datetime',y='attr2',source=self.plot_source)



        self.plot_source.selected.js_on_change('indices', CustomJS(args=dict(s1=self.plot_source, s2=self.dd, x=self.x_select, y=self.y_select, code="""
        var inds = cb_obj.indices;
        var d1 = s1.data;
        var d2 = s2.data;
        var x = x;
        var y = y;
        d2[x] = []
        d2[y] = []
        for (var i = 0; i < inds.length; i++) {
            d2[x].push(d1[x][inds[i]])
            d2[y].push(d1[y][inds[i]])
        }
        s2.change.emit();""")))

    def update(self):
        self.get_data(self.x_select.value, self.y_select.value, update=True)


    def run(self):
        self.get_data(self.x_select.value, self.y_select.value)
        self.time_series_plot()
        self.btn.on_click(self.update)
