
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
import pandas as pd
import numpy as np
import glob, os

from static.plots import Plots

class PosAccPage():
    def __init__(self, datahandler):
        self.DH = datahandler
        self.plots = Plots('Positioner Accuracy Performance',source=None)
        self.data_source = self.plots.data_source
        self.pos = str(1235)
        posfiles = glob.glob(os.getcwd()+'/instperfapp/data/per_fiber/*.csv')
        self.pos_list = [os.path.splitext(os.path.split(posf)[1])[0] for posf in posfiles] #np.linspace(0,4999,5000)
        self.x_options = ['OFFSET_0','OFFSET_FINAL']
        self.y_options = ['TARGET_RA', 'TARGET_DEC','FIBERASSIGN_X', 'FIBERASSIGN_Y','EXPOSURE','total_move_sequences',
                        'airmass','mirror_temp','truss_temp','air_mirror_temp_diff','wind_speed','wind_direction',
                        'humidity','guide_meanxy','hex_rot_offset','ctrl_enabled']
        self.pos_select = Select(value=self.pos, options=self.pos_list)
        self.x_select = Select(value='OFFSET_0', options=self.x_options)
        self.y_select = Select(value='TARGET_RA', options=self.y_options)

        self.btn = Button(label = 'Get Pos', button_type='primary',width=300)


    def page_layout(self):
        this_layout = layout([[self.plots.header],
                        [self.pos_select, self.x_select, self.y_select, self.btn],
                        [self.corr],
                        [self.ts1],
                        [self.ts2],
                        [self.scatt]])
        tab = Panel(child=this_layout, title=self.plots.title)
        return tab

    def get_pos_data(self, update=False):
        pos_file = os.getcwd()+'/instperfapp/data/per_fiber/{}.csv'.format(self.pos)
        data = pd.read_csv(pos_file)
        self.dev = int(np.unique(data.DEVICE_LOC)[0])
        self.petal = int(np.unique(data.PETAL_LOC)[0])
        data['air_mirror_temp_diff'] = np.abs(data['air_temp'] - data['mirror_temp'])
        data_ = data[['mjd_obs',self.x_select.value, self.y_select.value]]
        data_ = data.rename(columns={self.x_select.value:'attr1',self.y_select.value:'attr2'}) 
        if update:
            self.pos_source.data = data_
        else:
            self.pos_source = ColumnDataSource(data_)
        self.time_series_plot()
        self.pos_loc_plot()

    def time_series_plot(self):
        """
        Note, cannot get labels to update
        """
        self.corr = self.plots.figure(width=350, height=250, x_axis_label='attr1', y_axis_label='attr2')
        self.ts1 = self.plots.figure(x_axis_label='mjd_obs', y_axis_label='attr1')
        self.ts2 = self.plots.figure(x_axis_label='mjd_obs', y_axis_label='attr2')
        if self.pos_source is not None:
            self.plots.corr_plot(self.corr, x='attr1',y='attr2', source=self.pos_source)
            self.plots.circle_plot(self.ts1, x='mjd_obs',y='attr1',source=self.pos_source)
            self.plots.circle_plot(self.ts2, x='mjd_obs',y='attr2',source=self.pos_source)

    def pos_loc_plot(self):
        self.fp = self.DH.fiberpos
        print(self.fp.head())
        self.fp['COLOR'] = 'white'
        idx = self.fp[(self.fp.DEVICE == self.dev) & (self.fp.PETAL == self.petal)].index
        self.fp.at[idx, 'COLOR'] = 'red'
        self.scatt = self.plots.figure(width=450, height=450, x_axis_label='obsX / mm', y_axis_label='obsY / mm')
        self.plots.pos_scatter(self.scatt, self.fp, 'COLOR')

    def update(self):
        self.pos = self.pos_select.value
        self.get_pos_data(update=True)

    def run(self):
        self.get_pos_data()
        #self.time_series_plot()
        self.btn.on_click(self.update)
