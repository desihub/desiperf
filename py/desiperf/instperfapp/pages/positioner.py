
import os
import glob
import pandas as pd
import numpy as np

from bokeh.layouts import column, layout, row
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select, CustomJS, TextInput, RadioGroup
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

        self.pos = str(6205)

        self.select_header = Div(text="Select Positioner(s) to Plot", width=1000, css_classes=['subt-style'])
        self.enter_pos_option = RadioGroup(labels=["Enter POS ID","OR Select from lists"], active=0)
        self.pos_enter = TextInput(title="POS",value=self.pos)
        self.pos_select = Select(title='Select POS', value='ALL')
        self.can_select = Select(title='Select CAN', value='ALL', options=['ALL','10','11','12','13','14','15','16','17','20','21'])
        self.petal_select = Select(title='Select PETAL', value='ALL', options=['ALL','0','1','2','3','4','5','6','7','8','9'])

        self.fp = self.DH.fiberpos

        self.pos_tooltips = [
            ("POS ID","@CAN_ID"),
            ("Petal","@PETAL"),
            ("CAN","@BUS_ID"),
            ("DEV LOC","@DEVICE"),
            ("FIBER No.","@FIBER"),
            ("(x,y,z)","(@X,@Y,@Z)")]

    def page_layout(self):
        #docstring
        this_layout = layout([[self.header],
                        [self.description],
                        [ self.x_cat_select, self.y_cat_select],
                        [self.x_select, self.y_select, self.btn],
                        [self.select_header], 
                        [column([Div(text=' ',height=50), self.pos_enter, self.enter_pos_option, self.petal_select, self.can_select, self.pos_select]), self.scatt],
                        [self.attr_header],
                        [self.bin_option, self.bin_slider, self.save_btn],
                        [Div(text=' ',height=200),self.main_plot],
                        [self.desc_header],
                        [self.data_det_option, self.details],
                        [self.time_header],
                        [self.ts1],
                        [self.ts2]])
        tab = Panel(child=this_layout, title=self.title)
        return tab

    def pos_selection(self, attr, old, new):
        self.petal = self.petal_select.value
        self.can = self.can_select.value

        if (self.petal == 'ALL') & (self.can == 'ALL'):
            pos_list = []
        elif (self.petal == 'ALL') & (self.can != 'ALL'):
            pos_list = list(self.fp[(self.fp.BUS_ID == int(self.can))].CAN_ID)
        elif (self.petal != 'ALL') & (self.can == 'ALL'):
            pos_list = list(self.fp[(self.fp.PETAL == int(self.petal))].CAN_ID)
        else:
            pos_list = list(self.fp[(self.fp.PETAL == int(self.petal))&(self.fp.BUS_ID == int(self.can))].CAN_ID)
        
        self.pos_select.options = ['ALL'] + [str(p) for p in pos_list]

    def get_selection(self):
        if self.enter_pos_option.active == 0:
            self.pos = self.pos_enter.value
            self.can = int(np.unique(self.fp[self.fp.CAN_ID == int(self.pos)].BUS_ID)[0])
            self.petal = int(np.unique(self.fp[self.fp.CAN_ID == int(self.pos)].PETAL)[0])
        else:
            self.pos = self.pos_select.value
            self.can = self.can_select.value
            self.petal = self.petal_select.value

        if self.pos != 'ALL':
            self.pos_files = [os.path.join(self.DH.pos_dir, '{}.csv'.format(self.pos))]
            row = self.fp[self.fp.CAN_ID == int(self.pos)]
            self.index = row.index
            #self.can_select.value = str(row.BUS_ID)
            #self.petal_select.value = str(row.PETAL)
        elif self.petal != 'ALL':
            if self.can == 'ALL':
                pos = self.fp[self.fp.PETAL == int(self.petal)]
                self.index = pos.index
                self.pos_files = [os.path.join(self.DH.pos_dir, '{}.csv'.format(p)) for p in pos.CAN_ID]
            else:
                pos = self.fp[(self.fp.PETAL == int(self.petal))&(self.fp.BUS_ID == int(self.can))]
                self.pos_files = [os.path.join(self.DH.pos_dir, '{}.csv'.format(p)) for p in pos.CAN_ID]
                self.index = pos.index
        elif self.can != 'ALL':
            if self.petal == 'ALL':
                pos = self.fp[(self.fp.BUS_ID == int(self.can))]
                self.pos_files = [os.path.join(self.DH.pos_dir, '{}.csv'.format(p)) for p in pos.CAN_ID]
                self.index = pos.index

    def get_pos_data(self, update=False):
        #- docstring
        self.xx = 'DATETIME'
        dd = []
        for f in self.pos_files:
            try:
                dd.append(pd.read_csv(f))
            except:
                pass

        data = pd.concat(dd)
        data['air_mirror_temp_diff'] = np.abs(data['air_temp'] - data['mirror_temp'])
        
        data = self.DH.get_datetime(data)
        data.columns = [x.upper() for x in data.columns]
        data_ = data[['DATETIME',self.x_select.value, self.y_select.value]]
        data_ = data_[pd.notnull(data_['DATETIME'])] #temporary
        data_ = data_.rename(columns={self.x_select.value:'attr1',self.y_select.value:'attr2'}) 
        if update:
            self.plot_source.data = data_
            self.main_plot.xaxis.axis_label = self.x_select.value
            self.main_plot.yaxis.axis_label = self.y_select.value
            self.ts1.yaxis.axis_label = self.x_select.value
            self.ts2.yaxis.axis_label = self.y_select.value
            self.main_plot.title.text  = '{} vs. {} for {} positioners'.format(self.x_select.value, self.y_select.value, len(self.index))
            self.ts1.title.text = 'Time vs. {}'.format(self.x_select.value)
            self.ts2.title.text = 'Time vs. {}'.format(self.y_select.value)
            self.bin_data.data = self.update_binned_data('attr1','attr2', pd.DataFrame(self.plot_source.data))
            self.bin_data1.data = self.update_binned_data('DATETIME','attr1', pd.DataFrame(self.plot_source.data))
            self.bin_data2.data = self.update_binned_data('DATETIME','attr2', pd.DataFrame(self.plot_source.data))

            fp = self.DH.fiberpos
            fp['COLOR'] = 'white'
            fp.at[self.index, 'COLOR'] = 'red'
            self.fp_source.data = fp
        else:
            fp = self.DH.fiberpos
            fp['COLOR'] = 'white'
            fp.at[self.index, 'COLOR'] = 'red'
            self.fp_source = ColumnDataSource(fp)

            self.plot_source = ColumnDataSource(data_)
            self.sel_data = ColumnDataSource(data=dict(attr1=[], attr2=[]))

            self.bin_data = ColumnDataSource(self.update_binned_data('attr1','attr2', pd.DataFrame(self.plot_source.data)))
            self.bin_data1 = ColumnDataSource(self.update_binned_data('DATETIME','attr1', pd.DataFrame(self.plot_source.data)))
            self.bin_data2 = ColumnDataSource(self.update_binned_data('DATETIME','attr2', pd.DataFrame(self.plot_source.data)))

    def pos_loc_plot(self):
        self.scatt = self.figure(width=450, height=450, x_axis_label='obsX / mm', y_axis_label='obsY / mm', 
                                        tooltips=self.pos_tooltips)
        self.pos_scatter(self.scatt, self.fp_source, 'COLOR')

    def pos_update(self):
        self.get_selection()
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
            ("(x,y)", "($x, $y)"),]
        self.get_selection()
        self.get_pos_data()
        self.time_series_plot()
        self.pos_loc_plot()
        self.btn.on_click(self.pos_update)
        self.bin_plot('new',[0],[0])
        #self.replot_btn.on_click(self.pos_update)
        self.bin_option.on_change('active',self.bin_plot)
        self.petal_select.on_change('value',self.pos_selection)
        self.can_select.on_change('value',self.pos_selection)
        self.save_btn.on_click(self.save_data)
        self.plot_source.selected.on_change('indices', self.update_selected_data)
