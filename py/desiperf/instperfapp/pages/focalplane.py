
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models.widgets.markups import Div
from bokeh.models import ColumnDataSource, PreText, Select
from bokeh.plotting import figure
import pandas as pd 

from static.page import Page

class FocalPlanePage(Page):
    def __init__(self, source=None):
        self.page = Page('Fiber Positioner Accuracy', source)
        self.details = self.page.pretext(' ')
        self.cov = self.page.pretext(' ')
        self.data_source = self.page.data_source
        self.default_options = ['max_blind','max_blind_95','rms_blind',
             'rms_blind_95', 'max_corr', 'max_corr_95', 
             'rms_corr', 'rms_corr_95','airmass','domeaz']

        self.x_select = Select(value='max_blind',options=self.default_options)
        self.y_select = Select(value='airmass', options=self.default_options)
        self.btn = self.page.button('Plot')

    def get_data(self, attr1, attr2, update=False):
        data = pd.DataFrame(self.data_source.data)[['mjd_obs',attr1,attr2]]
        self.details.text = str(data.describe())
        self.cov.text = str(data.cov())
        data_ = data.rename(columns={attr1:'attr1',attr2:'attr2'}) 
        if update:
            self.plot_source.data = data_
        else:
            self.plot_source = ColumnDataSource(data_)


    def page_layout(self):
        this_layout = layout([[self.page.header],
                              [self.x_select, self.y_select, self.btn],
                              [self.corr,self.details, self.cov],
                              [self.ts1],
                              [self.ts2]])
        tab = Panel(child=this_layout, title=self.page.title)
        return tab

    def time_series_plot(self):
        self.corr = figure(plot_width=350, plot_height=250, tools=self.page.tools)
        self.ts1 = figure(plot_width=900, plot_height=200, tools=self.page.tools, x_axis_type='datetime', active_drag="xbox_select")
        self.ts2 = figure(plot_width=900, plot_height=200, tools=self.page.tools, x_axis_type='datetime', active_drag="xbox_select")
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

