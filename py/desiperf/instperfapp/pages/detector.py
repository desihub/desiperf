
from bokeh.layouts import layout
from bokeh.models.widgets import Panel
from bokeh.models import ColumnDataSource, Select, CDSView, GroupFilter
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
import pandas as pd

from static.plots import Plots


class DetectorPage(Plots):
    def __init__(self, datahandler):
        Plots.__init__(self,'Detector Noise Performance', datahandler.detector_source)
        self.description = Div(text='These plots show the behavior of the detectors in each spectrograph over time.', width=800, style=self.text_style)

        
        self.spectro_options = ['ALL', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        self.amps = ['A','B','C','D']
        self.colors = ['red','blue','green','yellow']
        self.sp_select = Select(title='Spectrograph', value='ALL', options=self.spectro_options)

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

        self.details.text = 'Data Overview: \n ' + str(data.describe())
        
        if update:
            self.plot_source.data = data_
            self.tsb.xaxis.axis_label = self.x_select.value
            self.tsb.yaxis.axis_label = self.y_select.value
            self.tsr.xaxis.axis_label = self.x_select.value
            self.tsr.yaxis.axis_label = self.y_select.value
            self.tsz.xaxis.axis_label = self.x_select.value
            self.tsz.yaxis.axis_label = self.y_select.value

        else:
            self.plot_source = ColumnDataSource(data_)
            self.viewb = []
            self.viewr = []
            self.viewz = []
            for amp in self.amps:
                self.viewb.append(CDSView(source=self.plot_source, filters=[GroupFilter(column_name='CAM', group='B'), GroupFilter(column_name='AMP', group=amp)]))
                self.viewr.append(CDSView(source=self.plot_source, filters=[GroupFilter(column_name='CAM', group='R'), GroupFilter(column_name='AMP', group=amp)]))
                self.viewz.append(CDSView(source=self.plot_source, filters=[GroupFilter(column_name='CAM', group='Z'), GroupFilter(column_name='AMP', group=amp)]))

        self.time_series_plot()

    def page_layout(self):
        this_layout = layout([[self.header],
                              [self.description],
                              [self.x_select, self.y_select, self.sp_select, self.btn],
                              [self.details],
                              [self.tsb], [self.tsr], [self.tsz]])

        tab = Panel(child=this_layout, title=self.title)
        return tab

    def time_series_plot(self):
        
        if self.x_select.value == 'datetime':
            self.tsb = figure(plot_width=1000, plot_height=400, tools=self.tools, tooltips=self.default_tooltips, 
                                x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, x_axis_type = 'datetime',title='Blue Detectors (note: select Amp to hide)')
            self.tsr = figure(plot_width=1000, plot_height=400, tools=self.tools, tooltips=self.default_tooltips,  
                                x_axis_label=self.x_select.value, y_axis_label=self.y_select.value,  x_axis_type = 'datetime',title='Red Detectors (note: select Amp to hide)')
            self.tsz = figure(plot_width=1000, plot_height=400, tools=self.tools, tooltips=self.default_tooltips,  
                            x_axis_label=self.x_select.value, y_axis_label=self.y_select.value,  x_axis_type = 'datetime',title='Infrared Detectors (note: select Amp to hide)')
        else:
            self.tsb = figure(plot_width=1000, plot_height=400, tools=self.tools, tooltips=self.default_tooltips, 
                                x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, title='Blue Detectors (note: select Amp to hide)')
            self.tsr = figure(plot_width=1000, plot_height=400, tools=self.tools, tooltips=self.default_tooltips,  
                                x_axis_label=self.x_select.value, y_axis_label=self.y_select.value,  title='Red Detectors (note: select Amp to hide)')
            self.tsz = figure(plot_width=1000, plot_height=400, tools=self.tools, tooltips=self.default_tooltips,  
                            x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, title='Infrared Detectors (note: select Amp to hide)')

        for i, view in enumerate(self.viewb):
            self.tsb.circle(x='attrbx', y='attrby', color=self.colors[i], size=5, source=self.plot_source, selection_color="cyan", legend = "{}".format(self.amps[i]), view=view)
        for i, view in enumerate(self.viewr):
            self.tsr.circle(x='attrrx', y='attrry',  color=self.colors[i], size=5, source=self.plot_source, selection_color="orange", legend = "{}".format(self.amps[i]), view=view)
        for i, view in enumerate(self.viewz):
            self.tsz.circle(x='attrzx', y='attrzy',  color=self.colors[i], size=5, source=self.plot_source, selection_color="gray", legend = "{}".format(self.amps[i]), view=view)

        
        for p in [self.tsb, self.tsr, self.tsz]:
            p.legend.title = "Amp"
            p.legend.location = "top_right"
            p.legend.orientation = "horizontal"
            p.legend.click_policy="hide"   

    def spec_update(self):
        self.spectro_data(self.x_select.value, self.y_select.value, self.sp_select.value, update=True)

    def run(self):

        self.prepare_layout()
        self.x_select.value = 'datetime'
        self.y_select.value = 'READNOISE'
        self.spectro_data(self.x_select.value, self.y_select.value, self.sp_select.value)
        self.time_series_plot()
        self.btn.on_click(self.spec_update)
