
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
import pandas as pd 

from static.page import Page

class DetectorPage(Page):
    def __init__(self, source):
        self.page = Page('Detector Noise Performance',source)
        self.btn = self.page.button('OK')
        self.details = self.page.pretext(' ')
        self.data_source = self.page.data_source
        self.default_options = ['READNOISE','BIAS','COSMICS_RATE'] #'NIGHT','EXPID','SPECTRO','CAM','AMP',

        self.x_select = Select(value='READNOISE',options=self.default_options)
        self.btn = self.page.button('Plot')

    def get_data(self, attr1,  update=False):
        data = pd.DataFrame(self.data_source.data)[['EXPID',attr1]]
        self.details.text = str(data.describe())
        data_ = data.rename(columns={attr1:'attr1'}) 
        if update:
            self.plot_source.data = data_
        else:
            self.plot_source = ColumnDataSource(data_)

    def page_layout(self):
        this_layout = layout([[self.page.header],
                      [self.x_select, self.btn],
                      [self.details],
                      [self.ts1]])
        tab = Panel(child=this_layout, title=self.page.title)
        return tab

    def time_series_plot(self):
        #self.corr = figure(plot_width=350, plot_height=250, tools=self.page.tools)
        self.ts1 = figure(plot_width=900, plot_height=200, tools=self.page.tools, active_drag="xbox_select", x_axis_label='EXPID', y_axis_label=self.x_select.value)
        #self.ts2 = figure(plot_width=900, plot_height=200, tools=self.page.tools, active_drag="xbox_select")
        if self.data_source is not None:
            #self.corr.circle(x='attr1', y='attr2', size=2, source=self.plot_source, selection_color="orange", alpha=0.6, nonselection_alpha=0.1, selection_alpha=0.4)
            self.ts1.circle(x='EXPID', y='attr1', size=5, source=self.plot_source, color="blue", selection_color="orange")
            #self.ts2.circle(x='EXPID', y='attr2', size=5, source=self.plot_source, color="blue", selection_color="orange")

    def update(self):
        print('here')
        self.get_data(self.x_select.value, update=True)
        print(self.plot_source.data)
        self.time_series_plot()

    def run(self):
        self.get_data(self.x_select.value)
        self.time_series_plot()
        self.btn.on_click(self.update)
