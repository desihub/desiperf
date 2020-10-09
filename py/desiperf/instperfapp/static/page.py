from bokeh.io import curdoc
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select, Slider, CheckboxGroup, ColumnDataSource, RadioGroup, CustomJS, Line
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
from scipy import stats
import pandas as pd 
import numpy as np 
from datetime import datetime
from astropy.time import Time 
import matplotlib.dates as mdates
from static.plots import Plots


class Page(Plots):
    def __init__(self, title, source=None):
        Plots.__init__(self, title, source)
        self.title = title
        self.header = Div(text="{}".format(title), width=500, css_classes=['h1-title-style'])
        self.data_source = source  # Here it will pick up the latest
        self.tools = 'pan,wheel_zoom,lasso_select,reset,undo,save,hover'
        self.bin_slider = Slider(start=1, end = 100, value=100, step=1, title="# of Bins", direction="rtl", width=300)
        self.line = Div(text='------------------------------------------------------------------------------------------------------------------', width=800)

        self.details = PreText(text=' ', width=500)
        self.cov = PreText(text=' ', width=400)

        self.btn = Button(label='Re-Plot', css_classes=['connect_button'])
        self.save_btn = Button(label='Save Selected Data', width=200, css_classes=['save_button'])

        self.bin_option = CheckboxButtonGroup(labels=["Raw Data","Binned Data"], active=[0], orientation='horizontal')
        self.data_det_option = RadioGroup(labels=["All Data","Selected Data"], active=0, width=150)
    
        self.obstype_hdr = Div(text="Select Obstype: ",  width=150)
        self.obstype_option = CheckboxButtonGroup(name='ObsType', labels=['ALL','SCIENCE','DARK','ZERO','FLAT','TWILIGHT','OTHER'], active=[0], orientation='horizontal')
        self.obstype = ['ALL']

        self.time_header = Div(text="Time Plots", width=1000, css_classes=['subt-style'])
        self.attr_header = Div(text="Attribute Plot", width=1000, css_classes=['subt-style'])
        self.desc_header = Div(text="Data Description", width=1000, css_classes=['subt-style'])

    def prepare_layout(self):
        self.x_cat_select = Select(title='X Category',options=self.x_cat_options, value=self.x_cat_options[0])
        self.y_cat_select = Select(title='Y Category',options=self.y_cat_options, value=self.x_cat_options[1])
        self.x_select = Select(title='X Attribute', options=self.x_options[self.x_cat_options[0]], value=self.x_options[self.x_cat_options[0]][0])
        self.y_select = Select(title='Y Attribute', options=self.y_options[self.y_cat_options[1]], value=self.x_options[self.x_cat_options[1]][0])  
        x_attribute_callback = CustomJS(args=dict(x_select=self.x_select),code = """
            const opts = %s
            console.log('changed selected options',cb_obj.value)
            x_select.options = opts[cb_obj.value]
            """ %self.x_options)

        self.x_cat_select.js_on_change('value',x_attribute_callback)

        y_attribute_callback = CustomJS(args=dict(y_select=self.y_select),code = """
            const opts = %s
            console.log('changed selected options',cb_obj.value)
            y_select.options = opts[cb_obj.value]
            """ %self.y_options)

        self.y_cat_select.js_on_change('value',y_attribute_callback)

    def save_data(self):
        dd = pd.DataFrame(self.sel_data.data)
        dd = dd.rename(columns={'attr1':self.x_select.value, 'attr2':self.y_select.value})
        dd.to_csv('saved_data/{}_data_selected.csv'.format(datetime.now().strftime('%Y%m%d_%H:%M:%S.%f')),index=False)

    def data_selections(self, data):
        if 'ALL' in self.obstype:
            pass
        else:
            data = data[data.OBSTYPE.isin(self.obstype)]
        return data

    def obstype_selection(self, attr, old, new):
        otypes = np.array(['ALL','SCIENCE','DARK','ZERO','FLAT','TWILIGHT','OTHER'])
        self.obstype = otypes[new]

    def change_btn_label(self,a):
        if a == 0:
            self.btn.label = 'Re-Plot'
        elif a == 1:
            self.btn.label = 'Plotting ... Please Wait'

    def data_det_type(self, attr, old, new):
        if new == 0:
            self.details.text = 'Data Overview: \n ' + str(pd.DataFrame(self.dd.data).describe())
            self.cov.text = 'Covariance of Option {} & {}: \n'.format(self.x_select.value, self.y_select.value, str(pd.DataFrame(self.dd.data).cov()))
        if new == 1:
            self.details.text = 'Data Overview: \n ' + str(pd.DataFrame(self.sel_data.data).describe())
            self.cov.text = 'Covariance of Option {} & {}: \n'.format(self.x_select.value, self.y_select.value, str(pd.DataFrame(self.sel_data.data).cov()))

    def update(self):
        self.change_btn_label(1)
        if self.page_name == 'fp':
            self.get_data(self.xx, self.x_select.value, self.y_select.value, self.other_attr, update=True)
        if self.page_name == 'pos':
            self.get_selection()
            self.get_data(self.xx, self.x_select.value, self.y_select.value, self.other_attr, update=True)
        if self.page_name == 'spec':
            self.spectro_data(self.x_select.value, self.y_select.value, self.sp_select.value, update=True)
        self.change_btn_label(0)

    def activate_buttons(self):
        self.btn.on_click(self.update)
        self.bin_option.on_change('active',self.bin_plot)

        self.obstype_option.on_change('active',self.obstype_selection)
        self.save_btn.on_click(self.save_data)
        self.data_det_option.on_change('active',self.data_det_type)
        self.plot_source.selected.on_change('indices', self.update_selected_data)
        self.plot_trend_option.on_change('active',self.plot_trend_line)

        