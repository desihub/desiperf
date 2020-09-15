
import os
import glob
import pandas as pd
import numpy as np

from bokeh.layouts import column, layout, row
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select, CustomJS
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure

from static.attributes import Positioner_attributes
from static.plots import Plots

class PosAccPage(Plots):
    def __init__(self, datahandler):
        Plots.__init__(self,'Positioner',source=None)
        self.DH = datahandler

        desc = """These plots show behavior for a single (selected) positioner over time.
            """
        self.description = Div(text=desc, width=800, css_classes=['inst-style'])

        self.default_categories = list(Positioner_attributes.keys())
        self.default_options = Positioner_attributes

        self.pos = str(1235)
        posfiles = glob.glob(os.path.join(self.DH.pos_dir, '*.csv'))
        self.pos_list = [os.path.splitext(os.path.split(posf)[1])[0] for posf in posfiles] #np.linspace(0,4999,5000)
        
        self.pos_select = Select(title='Select POS', value=self.pos, options=self.pos_list)
        self.can_select = Select(title='Select CAN', value='10', options=['10','11','12','13','14','15','16','17','20','21'])
        self.petal_select = Select(title='Select PETAL', value='0', options=['0','1','2','3','4','5','6','7','8','9'])


    def page_layout(self):
        #docstring
        this_layout = layout([[self.header],
                        [self.description],
                        [ self.x_cat_select, self.y_cat_select],
                        [self.x_select, self.y_select, self.btn],
                        [column([self.pos_select, self.can_select, self.petal_select]), self.scatt],
                        [column([self.data_det_option, self.save_btn, self.bin_slider, self.bin_option, self.replot_btn]), [self.main_plot]],
                        [self.ts1],
                        [self.ts2]])
        tab = Panel(child=this_layout, title=self.title)
        return tab

    def get_pos_data(self, update=False):
        #- docstring
        self.xx = 'datetime'
        pos_file = os.path.join(self.DH.pos_dir, '{}.csv'.format(self.pos))
        data = pd.read_csv(pos_file)
        data = self.DH.get_datetime(data)
        self.dev = int(np.unique(data.DEVICE_LOC)[0])
        self.petal = int(np.unique(data.PETAL_LOC)[0])
        data['air_mirror_temp_diff'] = np.abs(data['air_temp'] - data['mirror_temp'])
        data_ = data[['datetime',self.x_select.value, self.y_select.value]]
        data_ = data_[pd.notnull(data_['datetime'])] #temporary
        data_ = data_.rename(columns={self.x_select.value:'attr1',self.y_select.value:'attr2'}) 
        if update:
            self.plot_source.data = data_
            self.main_plot.xaxis.axis_label = self.x_select.value
            self.main_plot.yaxis.axis_label = self.y_select.value
            self.ts1.yaxis.axis_label = self.x_select.value
            self.ts2.yaxis.axis_label = self.y_select.value
            self.main_plot.title.text  = '{} vs. {} for POS {}'.format(self.x_select.value, self.y_select.value, self.pos)
            self.ts1.title.text = 'Time vs. {}'.format(self.x_select.value)
            self.ts2.title.text = 'Time vs. {}'.format(self.y_select.value)
            self.bin_data.data = self.update_binned_data('attr1','attr2')
            self.bin_data1.data = self.update_binned_data('datetime','attr1')
            self.bin_data2.data = self.update_binned_data('datetime','attr2')
        else:
            self.plot_source = ColumnDataSource(data_)
            self.sel_data = ColumnDataSource(data=dict(attr1=[], attr2=[]))

            self.bin_data = ColumnDataSource(self.update_binned_data('attr1','attr2'))
            self.bin_data1 = ColumnDataSource(self.update_binned_data('datetime','attr1'))
            self.bin_data2 = ColumnDataSource(self.update_binned_data('datetime','attr2'))

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
        self.x_options = self.default_options
        self.y_options = self.default_options
        self.x_cat_options = self.default_categories
        self.y_cat_options = self.default_categories
        self.prepare_layout_two_menus()
        self.x_cat_select.value = self.default_categories[0]
        self.y_cat_select.value = self.default_categories[1]
        self.x_select.value = self.default_options[self.default_categories[0]][0]
        self.y_select.value = self.default_options[self.default_categories[1]][0]
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
        self.replot_btn.on_click(self.plot_binned_data)
        self.bin_option.on_change('active',self.bin_plot)
        self.save_btn.on_click(self.save_data)
        self.plot_source.selected.on_change('indices', self.update_selected_data)
