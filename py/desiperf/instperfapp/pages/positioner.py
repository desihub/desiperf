
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
import pandas as pd
import glob, os

from static.page import Page

class PosAccPage(Page):
    def __init__(self, source):
        self.page = Page('Positioner Accuracy Performance',source)
        self.data_source = self.page.data_source
        self.pos = str(3881)
        posfiles = glob.glob(os.getcwd()+'/instperfapp/data/per_fiber/*.csv')
        self.pos_list = [os.path.splitext(os.path.split(posf)[1])[0] for posf in posfiles] #np.linspace(0,4999,5000)
        self.default_options = ['TARGET_RA', 'TARGET_DEC','FIBERASSIGN_X', 'FIBERASSIGN_Y','OFFSET_0','OFFSET_FINAL']
        self.pos_select = self.page.select(self.pos, self.pos_list)
        self.x_select = self.page.select('OFFSET_0',self.default_options)

        self.btn = self.page.button('Get Pos')


    def page_layout(self):
        this_layout = layout([[self.page.header],
                        [self.pos_select, self.x_select, self.btn],
                        [self.ts1]])
        tab = Panel(child=this_layout, title=self.page.title)
        return tab

    def get_pos_data(self, update=False):
        pos_file = os.getcwd()+'/instperfapp/data/per_fiber/{}.csv'.format(self.pos)
        data = pd.read_csv(pos_file)[['EXPOSURE',self.x_select.value]]
        data_ = data.rename(columns={self.x_select.value:'attr1'}) 
        if update:
            self.pos_source.data = data_
        else:
            self.pos_source = ColumnDataSource(data_)
        self.time_series_plot()

    def time_series_plot(self):
        #self.corr = figure(plot_width=350, plot_height=250, tools=self.page.tools)
        self.ts1 = figure(plot_width=900, plot_height=200, tools=self.page.tools, active_drag="xbox_select")
        #self.ts2 = figure(plot_width=900, plot_height=200, tools=self.page.tools, active_drag="xbox_select")
        if self.pos_source is not None:
            #self.corr.circle(x='attr1', y='attr2', size=2, source=self.plot_source, selection_color="orange", alpha=0.6, nonselection_alpha=0.1, selection_alpha=0.4)
            self.ts1.circle(x='EXPOSURE', y='attr1', size=5, source=self.pos_source, color="blue", selection_color="orange")
            #self.ts2.circle(x='mjd_obs', y='attr2', size=5, source=self.plot_source, color="blue", selection_color="orange")

    def update(self):
        self.pos = self.pos_select.value
        self.get_pos_data(update=True)

    def run(self):
        self.get_pos_data()
        #self.time_series_plot()
        self.btn.on_click(self.update)
