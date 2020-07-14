
from bokeh.layouts import layout
from bokeh.models.widgets import Panel
from bokeh.models import ColumnDataSource, Select, CDSView, GroupFilter
from bokeh.plotting import figure
import pandas as pd

from static.page import Page


class DetectorPage(Page):
    def __init__(self, source):
        self.page = Page('Detector Noise Performance', source)
        self.btn = self.page.button('OK')
        self.details = self.page.pretext(' ')
        self.data_source = self.page.data_source
        self.default_options = ['READNOISE', 'BIAS', 'COSMICS_RATE']
# 'NIGHT','EXPID','SPECTRO','CAM','AMP',
        self.spectro_options = ['ALL', '0', '1', '2', '3', '4', '5', '6', '7',
                                '8', '9']

        self.x_select = Select(value='READNOISE', options=self.default_options)
        self.sp_select = Select(value='ALL', options=self.spectro_options)
        self.btn = self.page.button('Plot')

    def get_data(self, attr1,  spectro, update=False):
        data = pd.DataFrame(self.data_source.data)[['EXPID', attr1, 'SPECTRO', 'CAM']]
        # Convert CAM from byte encoding
        camdf = data['CAM'].str.decode('utf-8')
        data['CAM'] = camdf
        # Filter by sp_select if not 'ALL'
        if spectro != 'ALL':
            data = data.loc[data['SPECTRO'] == int(spectro)]
        self.details.text = str(data.describe())
        data_ = data.rename(columns={attr1: 'attr1'})
        if update:
            self.plot_source.data = data_
        else:
            self.plot_source = ColumnDataSource(data_)
            self.viewb = CDSView(source=self.plot_source, filters=[GroupFilter(column_name='CAM', group='B')])
            self.viewr = CDSView(source=self.plot_source, filters=[GroupFilter(column_name='CAM', group='R')])
            self.viewz = CDSView(source=self.plot_source, filters=[GroupFilter(column_name='CAM', group='Z')])

    def page_layout(self):
        this_layout = layout([[self.page.header],
                              [self.x_select, self.sp_select, self.btn],
                              [self.details],
                              [self.tsb], [self.tsr], [self.tsz]])
        tab = Panel(child=this_layout, title=self.page.title)
        return tab

    def time_series_plot(self):
        self.tsb = figure(plot_width=900, plot_height=200, tools=self.page.tools, x_axis_label='EXPID', y_axis_label=self.x_select.value)
        self.tsr = figure(plot_width=900, plot_height=200, tools=self.page.tools, x_axis_label='EXPID', y_axis_label=self.x_select.value)
        self.tsz = figure(plot_width=900, plot_height=200, tools=self.page.tools, x_axis_label='EXPID', y_axis_label=self.x_select.value)
        if self.data_source is not None:
            self.tsb.circle(x='EXPID', y='attr1', size=5, source=self.plot_source, selection_color="cyan", view=self.viewb)
            self.tsr.circle(x='EXPID', y='attr1', size=5, source=self.plot_source, selection_color="orange", view=self.viewr)
            self.tsz.circle(x='EXPID', y='attr1', size=5, source=self.plot_source, selection_color="gray", view=self.viewz)

    def update(self):
        self.get_data(self.x_select.value, self.sp_select.value, update=True)
        self.time_series_plot()

    def run(self):
        self.get_data(self.x_select.value, self.sp_select.value)
        self.time_series_plot()
        self.btn.on_click(self.update)
