
from bokeh.layouts import layout
from bokeh.models.widgets import Panel
from bokeh.models import ColumnDataSource, Select, CDSView, GroupFilter
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
import pandas as pd

from static.plots import Plots
from static.attributes import Spectrograph_attributes


class SpectrographPage(Plots):
    def __init__(self, datahandler):
        Plots.__init__(self,'Detector Noise Performance', datahandler.detector_source)
        self.description = Div(text='These plots show the behavior of the detectors in each spectrograph over time.', width=800, style=self.text_style)

        
        self.spectro_options = ['ALL', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        self.colors = {'A':'red','B':'blue','C':'green','D':'yellow'}
        self.sp_select = Select(title='Spectrograph', value='ALL', options=self.spectro_options)

        self.default_categories = list(Spectrograph_attributes.keys())

        self.default_options = Spectrograph_attributes

        self.x_options = ['EXPID','datetime','CAMERA_TEMP','CAMERA_HUMIDITY','BENCH_CRYO_TEMP','BENCH_COLL_TEMP','BENCH_NIR_TEMP', 'IEB_TEMP',
                            'READNOISE', 'BIAS', 'COSMICS_RATE', 'MEANDX', 'MINDX', 'MAXDX',
                            'MEANDY', 'MINDY', 'MAXDY', 'MEANXSIG', 'MINXSIG', 'MAXXSIG',
                            'MEANYSIG', 'MINYSIG', 'MAXYSIG', 'INTEG_RAW_FLUX',
                            'MEDIAN_RAW_FLUX', 'MEDIAN_RAW_SNR', 'FLUX', 'SNR', 'SPECFLUX','THRU']
        self.y_options = self.x_options

    def get_camera_attributes(self,attr):
        attr = str(attr).lower()
        attrs = [pre+'_'+attr for pre in ['blue','red','nir']]
        return attrs

    def spectro_data(self, attr1, attr2, spectro, update=False):
        data = pd.DataFrame(self.data_source.data)

        # Convert CAM from byte encoding
        #camdf = data['CAM'].str.decode('utf-8')
        #data['CAM'] = [x[2] for x in list(data['CAM'])]  #Something odd going on with teh pandas data :(
        # Filter by sp_select if not 'ALL'
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
            self.tsb.xaxis.axis_label = self.x_select.value
            self.tsb.yaxis.axis_label = self.y_select.value
            self.tsr.xaxis.axis_label = self.x_select.value
            self.tsr.yaxis.axis_label = self.y_select.value
            self.tsz.xaxis.axis_label = self.x_select.value
            self.tsz.yaxis.axis_label = self.y_select.value

        else:
            self.blue_source = ColumnDataSource(data_[data_.CAM == 'B'])
            self.red_source = ColumnDataSource(data_[data_.CAM == 'R'])
            self.zed_source = ColumnDataSource(data_[data_.CAM == 'Z'])

    def page_layout(self):
        this_layout = layout([[self.header],
                              [self.description],
                              [self.x_cat_select, self.y_cat_select, self.sp_select],
                              [self.x_select, self.y_select, self.btn]
                              [self.details],
                              [self.tsb], [self.tsr], [self.tsz]])

        tab = Panel(child=this_layout, title=self.title)
        return tab

    def time_series_plot(self):
        
        if self.x_select.value == 'datetime':
            axistype = 'datetime'
        else:
            axistype = None
        self.tsb = figure(plot_width=1000, plot_height=400, tools=self.tools, tooltips=self.default_tooltips, 
                            x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, x_axis_type=axistype, title='Blue Detectors')
        self.tsr = figure(plot_width=1000, plot_height=400, tools=self.tools, tooltips=self.default_tooltips,  
                            x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, x_axis_type=axistype, title='Red Detectors')
        self.tsz = figure(plot_width=1000, plot_height=400, tools=self.tools, tooltips=self.default_tooltips,  
                            x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, x_axis_type=axistype, title='Infrared Detectors')

        self.tsb.circle(x='attrbx', y='attrby', color='color', size=5, source=self.blue_source, selection_color="gray", legend = 'AMP')
        self.tsr.circle(x='attrrx', y='attrry',  color='color', size=5, source=self.red_source, selection_color="gray", legend = 'AMP')
        self.tsz.circle(x='attrzx', y='attrzy',  color='color', size=5, source=self.zed_source, selection_color="gray", legend = 'AMP')

        
        for p in [self.tsb, self.tsr, self.tsz]:
            p.legend.title = "Amp"
            p.legend.location = "top_right"
            p.legend.orientation = "horizontal" 

    def spec_update(self):
        self.spectro_data(self.x_select.value, self.y_select.value, self.sp_select.value, update=True)

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
        self.spectro_data(self.x_select.value, self.y_select.value, self.sp_select.value)
        self.time_series_plot()
        self.btn.on_click(self.spec_update)
