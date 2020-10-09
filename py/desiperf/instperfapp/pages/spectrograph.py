
from bokeh.layouts import layout, column
from bokeh.models.widgets import Panel
from bokeh.models import ColumnDataSource, Select, CDSView, GroupFilter
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
import pandas as pd

from static.page import Page
from static.plots import Plots
from static.attributes import Spectrograph_attributes


class SpectrographPage(Page):
    def __init__(self, datahandler):
        Page.__init__(self,'Spectrograph', datahandler.detector_source)
        self.page_name = 'spec'
        self.description = Div(text='These plots show the behavior of the detectors in each spectrograph over time.', width=800, css_classes=['inst-style'])

        
        self.spectro_options = ['ALL', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        self.colors = {'A':'red','B':'blue','C':'green','D':'yellow'}
        self.sp_select = Select(title='Spectrograph', value='ALL', options=self.spectro_options)

        self.default_categories = list(Spectrograph_attributes.keys())

        self.default_options = Spectrograph_attributes

    def get_camera_attributes(self,attr):
        attr = str(attr)
        attrs = [pre+'_'+attr for pre in ['BLUE','RED','NIR']]
        return attrs

    def spectro_data(self, attr1, attr2, spectro, update=False):
        data = pd.DataFrame(self.data_source.data)
        data = self.data_selections(data)
        if spectro != 'ALL':
            data = data.loc[data['SPECTRO'] == int(spectro)]

        if attr1 in ['CAMERA_TEMP','CAMERA_HUMIDITY']:
            attrbx, attrrx, attrzx = self.get_camera_attributes(attr1)
            attrby, attrry, attrzy = attr2, attr2, attr2
            data = data[[attrbx, attrrx, attrzx, attr2, 'SPECTRO', 'CAM','AMP']]
            data_ = data.rename(columns={attrbx: 'attrbx', attrrx: 'attrrx',attrzx:'attrzx'})
            for b in ['attrby','attrry','attrzy']:
                data_[b] = data[attr2]
            del data_[attr2]
        elif attr2 in ['CAMERA_TEMP','CAMERA_HUMIDITY']:
            attrby, attrry, attrzy = self.get_camera_attributes(attr2)
            attrbx, attrrx, attrzx = attr1, attr1, attr1
            data = data[[attr1, attrby, attrry, attrzy, 'SPECTRO', 'CAM','AMP']]
            data_ = data.rename(columns={attrby: 'attrby', attrry: 'attrry',attrzy:'attrzy'})
            for a in ['attrbx','attrrx','attrzx']:
                data_[a] = data[attr1]
            del data_[attr1]
        else:
            attrbx, attrrx, attrzx = attr1, attr1, attr1
            attrby, attrry, attrzy = attr2, attr2, attr2
            data = data[[attr1, attr2, 'SPECTRO', 'CAM','AMP']]
            data_ = data.copy()
            for a in ['attrbx','attrrx','attrzx']:
                data_[a] = data_[attr1]
            for b in ['attrby','attrry','attrzy']:
                data_[b] = data_[attr2]
            del data_[attr1]
            del data_[attr2]

        data_['color'] = [self.colors[i] for i in list(data_.AMP)]
        self.details.text = 'Data Overview: \n ' + str(data.describe())
        
        if update:
            self.blue_source.data = data_[data_.CAM == 'B']
            self.red_source.data = data_[data_.CAM == 'R']
            self.zed_source.data = data_[data_.CAM == 'Z']
            self.ts0.xaxis.axis_label = self.x_select.value
            self.ts0.yaxis.axis_label = self.y_select.value
            self.ts1.xaxis.axis_label = self.x_select.value
            self.ts1.yaxis.axis_label = self.y_select.value
            self.ts2.xaxis.axis_label = self.x_select.value
            self.ts2.yaxis.axis_label = self.y_select.value

            self.bin_data.data = self.update_binned_data('attrbx','attrby', pd.DataFrame(self.blue_source.data))
            self.bin_data1.data = self.update_binned_data('attrrx','attrry', pd.DataFrame(self.blue_source.data))
            self.bin_data2.data = self.update_binned_data('attrzx','attrzy', pd.DataFrame(self.blue_source.data))

        else:
            self.sel_data = ColumnDataSource(data=dict(attr1=[], attr2=[]))

            self.blue_source = ColumnDataSource(data_[data_.CAM == 'B'])
            self.red_source = ColumnDataSource(data_[data_.CAM == 'R'])
            self.zed_source = ColumnDataSource(data_[data_.CAM == 'Z'])
            self.bin_data = ColumnDataSource(self.update_binned_data('attrbx','attrby', pd.DataFrame(self.blue_source.data)))
            self.bin_data1 = ColumnDataSource(self.update_binned_data('attrrx','attrry', pd.DataFrame(self.red_source.data)))
            self.bin_data2 = ColumnDataSource(self.update_binned_data('attrzx','attrzy', pd.DataFrame(self.zed_source.data)))

    def page_layout(self):
        this_layout = layout([[self.header],
                              [self.description],
                              [self.x_cat_select, self.y_cat_select, self.sp_select],
                              [self.x_select, self.y_select, self.btn],
                              [self.obstype_hdr, self.obstype_option], 

                              [self.line],
                              [self.bin_option,self.bin_slider, self.save_btn], 
                              [self.attr_header],
                              [self.ts0],
                              [self.ts1], 
                              [self.ts2],

                              [self.line],
                              [self.desc_header],
                              [self.data_det_option, self.details]])

        tab = Panel(child=this_layout, title=self.title)
        return tab

    def run(self):
        self.x_options = self.default_options
        self.y_options = self.default_options
        self.x_cat_options = self.default_categories
        self.y_cat_options = self.default_categories
        self.prepare_layout()

        self.spectro_data(self.x_select.value, self.y_select.value, self.sp_select.value)

        self.page_tooltips = [
            ("spec","@SPECTRO"),
            ("obstime","@DATETIME{%F}"),
            ("x attr.","@attrbx"),
            ("y attr.","@attrby"),]

        self.time_series_plot()

        self.activate_buttons()
        self.data_det_option.on_change('active',self.data_det_type)
        self.blue_source.selected.on_change('indices', self.update_selected_data)
        self.red_source.selected.on_change('indices', self.update_selected_data)
        self.zed_source.selected.on_change('indices', self.update_selected_data)


