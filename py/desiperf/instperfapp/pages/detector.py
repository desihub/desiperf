
from bokeh.layouts import layout
from bokeh.models.widgets import Panel
from bokeh.models import ColumnDataSource, Select, CDSView, GroupFilter
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
import pandas as pd

from static.plots import Plots


class DetectorPage():
    def __init__(self, datahandler):
        self.plots = Plots('Detector Noise Performance', datahandler.detector_source)
        self.description = Div(text='These plots show the behavior of the detectors in each spectrograph over time.', width=800, style=self.plots.text_style)
        self.details = PreText(text='Data Overview: \n ', width=500)
        self.data_source = self.plots.data_source
        self.y_default_options = ['READNOISE', 'BIAS', 'COSMICS_RATE']
        self.x_default_options = ['EXPID','TIME_RECORDED','CAMERA_TEMP','CAMERA_HUMIDITY','BENCH_CRYO_TEMP','BENCH_COLL_TEMP','BENCH_NIR_TEMP']
# 'NIGHT','EXPID','SPECTRO','CAM','AMP',
        self.spectro_options = ['ALL', '0', '1', '2', '3', '4', '5', '6', '7',
                                '8', '9']

        self.y_select = Select(title='Option 1', value='READNOISE', options=self.y_default_options)
        self.x_select = Select(title='Option 2', value='EXPID',options=self.x_default_options)
        self.sp_select = Select(title='Spectrograph', value='ALL', options=self.spectro_options)
        self.btn = Button(label='Plot', button_type='primary',width=200)

    def get_camera_attributes(self,attr):
        attr = str(attr).lower()
        attrs = [pre+'_'+attr for pre in ['blue','red','nir']]
        return attrs

    def get_data(self, attr1, attr2, spectro, update=False):
        data = pd.DataFrame(self.data_source.data)

        # Convert CAM from byte encoding
        #camdf = data['CAM'].str.decode('utf-8')
        data['CAM'] = [x[2] for x in list(data['CAM'])]  #Something odd going on with teh pandas data :(
        # Filter by sp_select if not 'ALL'
        if spectro != 'ALL':
            data = data.loc[data['SPECTRO'] == int(spectro)]

        if attr1 in ['CAMERA_TEMP','CAMERA_HUMIDITY']:
            attrb, attrr, attrz = get_camera_attributes(attr2)
            data = data[[attrb, attrr, attrz, attr2, 'SPECTRO', 'CAM']]
            data_ = data.rename(columns={ attrb: 'attrb', attrr: 'attrr',attrz:'attrz',attr2: 'attr2'})
            same = False
        else:
            data = data[[attr1, attr2, 'SPECTRO', 'CAM']]
            data_ = data.rename(columns={attr1: 'attrb', attr2: 'attr2'})
            same = True

        self.details.text = 'Data Overview: \n ' + str(data.describe())
        
        if update:
            self.plot_source.data = data_
        else:
            self.plot_source = ColumnDataSource(data_)
            self.viewb = CDSView(source=self.plot_source, filters=[GroupFilter(column_name='CAM', group='B')])
            self.viewr = CDSView(source=self.plot_source, filters=[GroupFilter(column_name='CAM', group='R')])
            self.viewz = CDSView(source=self.plot_source, filters=[GroupFilter(column_name='CAM', group='Z')])

        self.time_series_plot(same=same)

    def page_layout(self):
        this_layout = layout([[self.plots.header],
                              [self.description],
                              [self.x_select, self.y_select, self.sp_select, self.btn],
                              [self.details],
                              [self.tsb], [self.tsr], [self.tsz]])
        tab = Panel(child=this_layout, title=self.plots.title)
        return tab

    def time_series_plot(self, same=True):
        self.tsb = figure(plot_width=900, plot_height=200, tools=self.plots.tools, tooltips=self.plots.default_tooltips, x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, title='Blue Detectors')
        self.tsr = figure(plot_width=900, plot_height=200, tools=self.plots.tools, tooltips=self.plots.default_tooltips,  x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, title='Red Detectors')
        self.tsz = figure(plot_width=900, plot_height=200, tools=self.plots.tools, tooltips=self.plots.default_tooltips,  x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, title='Infrared Detectors')
        if self.data_source is not None:
            self.tsb.circle(x='attrb', y='attr2', size=5, source=self.plot_source, selection_color="cyan", view=self.viewb)
            if same:
                self.tsr.circle(x='attrb', y='attr2', size=5, source=self.plot_source, selection_color="orange", view=self.viewr)
                self.tsz.circle(x='attrb', y='attr2', size=5, source=self.plot_source, selection_color="gray", view=self.viewz)
            else:
                self.tsr.circle(x='attrr', y='attr2', size=5, source=self.plot_source, selection_color="orange", view=self.viewr)
                self.tsz.circle(x='attrz', y='attr2', size=5, source=self.plot_source, selection_color="gray", view=self.viewz)

    def update(self):
        self.get_data(self.x_select.value, self.y_select.value, self.sp_select.value, update=True)
        

    def run(self):
        self.get_data(self.x_select.value, self.y_select.value, self.sp_select.value)
        self.time_series_plot()
        self.btn.on_click(self.update)
