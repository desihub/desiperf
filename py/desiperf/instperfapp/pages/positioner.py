
import os
import glob
import pandas as pd
import numpy as np

from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select, CustomJS
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure


from static.plots import Plots

class PosAccPage(Plots):
    def __init__(self, datahandler):
        Plots.__init__(self,'Positioner Accuracy Performance',source=None)
        self.DH = datahandler
        self.description = Div(text='These plots show behavior for a single (selected) positioner over time.', 
                                width=800, style=self.text_style)

        self.pos = str(1235)
        posfiles = glob.glob(os.path.join(self.DH.pos_dir, '*.csv'))
        self.pos_list = [os.path.splitext(os.path.split(posf)[1])[0] for posf in posfiles] #np.linspace(0,4999,5000)
        
        self.pos_select = Select(title='Select POS', value=self.pos, options=self.pos_list)


    def page_layout(self):
        #docstring
        this_layout = layout([[self.header],
                        [self.description],
                        [self.pos_select, self.x_select, self.y_select, self.btn],
                        [self.bin_option, self.save_btn],
                        [self.bin_slider, self.replot_btn],
                        [self.corr,self.scatt],
                        [self.ts1],
                        [self.ts2]])
        tab = Panel(child=this_layout, title=self.title)
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
            self.plot_source.data = data_
            self.corr.xaxis.axis_label = self.x_select.value
            self.corr.yaxis.axis_label = self.y_select.value
            self.ts1.yaxis.axis_label = self.x_select.value
            self.ts2.yaxis.axis_label = self.y_select.value
            self.corr.title.text  = '{} vs. {} for POS {}'.format(self.x_select.value, self.y_select.value, self.pos)
            self.ts1.title.text = 'Time vs. {}'.format(self.x_select.value)
            self.ts2.title.text = 'Time vs. {}'.format(self.y_select.value)
            self.update_binned_data()
        else:
            self.plot_source = ColumnDataSource(data_)
            self.sel_data = ColumnDataSource(data=dict(attr1=[], attr2=[]))

            bd = self.update_binned_data()
            self.bin_data = ColumnDataSource(bd)

        self.pos_loc_plot()


    def pos_loc_plot(self):
        #- docstring
        self.fp = self.DH.fiberpos
        self.fp['COLOR'] = 'white'
        idx = self.fp[(self.fp.DEVICE == self.dev) & (self.fp.PETAL == self.petal)].index
        self.fp.at[idx, 'COLOR'] = 'red'
        self.scatt = self.figure(width=450, height=450, x_axis_label='obsX / mm', y_axis_label='obsY / mm', 
                                        tooltips=self.page_tooltips)
        self.pos_scatter(self.scatt, self.fp, 'COLOR')

    def pos_update(self):
        #- docstring
        self.pos = self.pos_select.value
        self.get_pos_data(update=True)

    def run(self):
        #- docstring
        self.y_options = ['OFFSET_0','OFFSET_FINAL']
        self.x_options = ['datetime','EXPOSURE','TARGET_RA', 'TARGET_DEC','FIBERASSIGN_X', 'FIBERASSIGN_Y',
                        'total_move_sequences','mirror_temp','truss_temp','air_mirror_temp_diff','wind_speed','wind_direction','ctrl_enabled',]
        self.xx = 'EXPID'
        self.prepare_layout()
        self.x_select.value = 'EXPOSURE'
        self.y_select.value = 'OFFSET_0'
        self.page_tooltips = [
            ("exposure","@EXPID"),
            ("{}".format(self.x_select.value),"@attr1"),
            ("{}".format(self.y_select.value),"@attr2"),
            ("(x,y)", "($x, $y)"),
            ]
        self.get_pos_data()
        self.time_series_plot()
        self.btn.on_click(self.pos_update)
        self.bin_plot('new',[0],[0])
        self.replot_btn.on_click(self.update_binned_data)
        self.bin_option.on_change('active',self.bin_plot)
        self.save_btn.on_click(self.save_data)
        self.plot_source.selected.js_on_change('indices', CustomJS(args=dict(s1=self.plot_source, s2=self.sel_data), code="""
                                                var inds = cb_obj.indices;
                                                var d1 = s1.data;
                                                var d2 = s2.data;
                                                d2['attr1'] = []
                                                d2['attr2'] = []
                                                for (var i = 0; i < inds.length; i++) {
                                                    d2['attr1'].push(d1['attr1'][inds[i]])
                                                    d2['attr2'].push(d1['attr2'][inds[i]])
                                                }
                                                s2.change.emit();
                                                s2.data = d2 """))

