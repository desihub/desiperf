
import os
import glob
import pandas as pd
import numpy as np

from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure


from static.plots import Plots

class PosAccPage():
    def __init__(self, datahandler):
        '''
        Args:
            datahandler :

        '''
        self.DH = datahandler
        self.plots = Plots('Positioner Accuracy Performance',source=None)
        self.description = Div(text='These plots show behavior for a single (selected) positioner over time.', 
                                width=800, style=self.plots.text_style)
        self.data_source = self.plots.data_source
        self.pos = str(1235)
        posfiles = glob.glob(os.path.join(self.DH.pos_dir, '*.csv'))
        self.pos_list = [os.path.splitext(os.path.split(posf)[1])[0] for posf in posfiles] #np.linspace(0,4999,5000)
        self.x_options = ['OFFSET_0','OFFSET_FINAL']
        self.y_options = ['datetime','EXPOSURE','TARGET_RA', 'TARGET_DEC','FIBERASSIGN_X', 'FIBERASSIGN_Y',
                        'total_move_sequences','mirror_temp','truss_temp','air_mirror_temp_diff','wind_speed','wind_direction','ctrl_enabled',]

        self.pos_select = Select(title='Select POS', value=self.pos, options=self.pos_list)
        self.x_select = Select(title='Option 1', value='OFFSET_0', options=self.x_options)
        self.y_select = Select(title='Option 2', value='TARGET_RA', options=self.y_options)

        self.btn = Button(label = 'Get Pos', button_type='primary',width=300)
        self.tooltips = None


    def page_layout(self):
        #docstring
        this_layout = layout([[self.plots.header],
                        [self.description],
                        [self.pos_select, self.x_select, self.y_select, self.btn],
                        [self.corr,self.scatt],
                        [self.ts1],
                        [self.ts2]])
        tab = Panel(child=this_layout, title=self.plots.title)
        return tab

    def get_pos_data(self, update=False):
        #- docstring
        pos_file = os.path.join(self.DH.pos_dir, '{}.csv'.format(self.pos))
        data = pd.read_csv(pos_file)
        data = self.DH.get_datetime(data)
        self.dev = int(np.unique(data.DEVICE_LOC)[0])
        self.petal = int(np.unique(data.PETAL_LOC)[0])
        data['air_mirror_temp_diff'] = np.abs(data['air_temp'] - data['mirror_temp'])
        data_ = data[['EXPID','datetime',self.x_select.value, self.y_select.value]]
        data_ = data.rename(columns={self.x_select.value:'attr1',self.y_select.value:'attr2'}) 
        if update:
            self.pos_source.data = data_
            self.corr.xaxis.axis_label = self.x_select.value
            self.corr.yaxis.axis_label = self.y_select.value
            self.ts1.yaxis.axis_label = self.x_select.value
            self.ts2.yaxis.axis_label = self.y_select.value
            self.corr.title.text  = '{} vs. {} for POS {}'.format(self.x_select.value, self.y_select.value, self.pos)
            self.ts1.title.text = 'Time vs. {}'.format(self.x_select.value)
            self.ts2.title.text = 'Time vs. {}'.format(self.y_select.value)
        else:
            self.pos_source = ColumnDataSource(data_)

        self.tooltips = [
            ("exposure","@EXPID"),
            ("{}".format(self.x_select.value),"@attr1"),
            ("{}".format(self.y_select.value),"@attr2"),
            ("(x,y)", "($x, $y)"),
            ]

        self.time_series_plot()
        self.pos_loc_plot()


    def time_series_plot(self):
        self.corr = self.plots.figure(width=450, height=450, tooltips=self.tooltips, x_axis_label=self.x_select.value, 
                                    y_axis_label=self.y_select.value, title='{} vs. {} for POS {}'.format(self.x_select.value, self.y_select.value, self.pos))
        self.ts1 = self.plots.figure(x_axis_label='EXPID', tooltips=self.tooltips, y_axis_label=self.x_select.value, 
                                    title='Exposure vs. {} for POS {}'.format(self.x_select.value, self.pos))
        self.ts2 = self.plots.figure(x_axis_label='EXPID', tooltips=self.tooltips, y_axis_label=self.y_select.value, 
                                    title='Exposure vs. {} for POS {}'.format(self.y_select.value, self.pos))
        if self.pos_source is not None:
            self.plots.corr_plot(self.corr, x='attr1',y='attr2', source=self.pos_source)
            self.plots.circle_plot(self.ts1, x='EXPID',y='attr1',source=self.pos_source)
            self.plots.circle_plot(self.ts2, x='EXPID',y='attr2',source=self.pos_source)

    def pos_loc_plot(self):
        #- docstring
        self.fp = self.DH.fiberpos
        self.fp['COLOR'] = 'white'
        idx = self.fp[(self.fp.DEVICE == self.dev) & (self.fp.PETAL == self.petal)].index
        self.fp.at[idx, 'COLOR'] = 'red'
        self.scatt = self.plots.figure(width=450, height=450, x_axis_label='obsX / mm', y_axis_label='obsY / mm', 
                                        tooltips=self.plots.pos_tooltips)
        self.plots.pos_scatter(self.scatt, self.fp, 'COLOR')

    def update(self):
        #- docstring
        self.pos = self.pos_select.value
        self.get_pos_data(update=True)

    def run(self):
        #- docstring
        self.get_pos_data()
        #self.time_series_plot()
        self.btn.on_click(self.update)
