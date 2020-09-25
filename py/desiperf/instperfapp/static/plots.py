from bokeh.io import curdoc
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select, Slider, CheckboxGroup, ColumnDataSource, RadioGroup, CustomJS
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
from scipy import stats
import pandas as pd 
import numpy as np 
from datetime import datetime
from astropy.time import Time 


class Plots:
    def __init__(self, title, source=None):
        self.title = title
        self.header = Div(text="{}".format(title), width=500, css_classes=['h1-title-style'])
        self.data_source = source  # Here it will pick up the latest
        self.tools = 'pan,wheel_zoom,lasso_select,reset,undo,save,hover'
        self.bin_slider = Slider(start=1, end = 100, value=100, step=1, title="# of Bins", direction="rtl", width=300)

        self.details = PreText(text=' ', width=500)
        self.cov = PreText(text=' ', width=400)

        self.btn = Button(label='Re-Plot', css_classes=['connect_button'])
        self.save_btn = Button(label='Save Selected Data', width=200, css_classes=['save_button'])

        self.bin_option = CheckboxButtonGroup(labels=["Raw Data","Binned Data"], active=[0], orientation='horizontal')
        self.data_det_option = RadioGroup(labels=["All Data","Selected Data"], active=0, width=150)
        self.sequence_option = CheckboxGroup(labels=['ALL','Action','DESI','FVC','GFA','Guide','Loops','Spectrographs'], active=[0])
        self.obstype_option = CheckboxButtonGroup(name='ObsType', labels=['ALL','SCIENCE','DARK','ZERO','FLAT','TWILIGHT','OTHER'], active=[0], orientation='horizontal')
        self.obstype = ['ALL']
        self.fp_tooltips = None
        self.bin_data = None

        self.time_header = Div(text="Time Plots", width=1000, css_classes=['subt-style'])
        self.attr_header = Div(text="Attribute Plot", width=1000, css_classes=['subt-style'])
        self.desc_header = Div(text="Data Description", width=1000, css_classes=['subt-style'])

        self.default_tooltips = [
                    ("index", "$index"),
                    ("(x,y)", "($x, $y)")]

        self.plot_source = None
        self.blue_source = None
        self.red_source = None 
        self.zed_source = None

    def prepare_layout(self):
        self.x_select = Select(title='X Attribute', options=self.x_options)
        self.y_select = Select(title='Y Attribute', options=self.y_options)

    def prepare_layout_two_menus(self):
        self.x_cat_select = Select(title='X Category',options=self.x_cat_options)
        self.y_cat_select = Select(title='Y Category',options=self.y_cat_options)
        self.x_select = Select(title='X Attribute', options=self.x_options[self.x_cat_options[0]])
        self.y_select = Select(title='Y Attribute', options=self.y_options[self.y_cat_options[1]])  
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

    def update(self):
        self.get_data(self.xx, self.x_select.value, self.y_select.value, self.other_attr, update=True)

    def save_data(self):
        dd = pd.DataFrame(self.sel_data.data)
        dd = dd.rename(columns={'attr1':self.x_select.value, 'attr2':self.y_select.value})
        dd.to_csv('{}_data_selected.csv'.format(datetime.now().strftime('%Y%m%d_%H:%M:%S.%f')),index=False)

    def update_binned_data(self, attr1, attr2, data):
        dd = data[pd.notnull(data[attr1])]
        dd = dd[pd.notnull(dd[attr2])]
        x = np.array(dd[attr1])
        y = np.array(dd[attr2])
        
        if attr1 == 'DATETIME':
            x = [Time(xx).mjd for xx in x]
    
        bin_means, bin_edges, binnumber = stats.binned_statistic(x, y, statistic='mean', bins=self.bin_slider.value)
        bin_std, bin_edges2, binnumber2 = stats.binned_statistic(x, y, statistic='std', bins=self.bin_slider.value)
        bin_width = (bin_edges[1] - bin_edges[0])
        bin_centers = bin_edges[1:] - bin_width/2
        upper = []
        lower = []
        for x, y, yerr in zip(bin_centers, bin_means, bin_std):
            lower.append(y - yerr)
            upper.append(y + yerr)
        if attr1 == 'DATETIME':
            bc = [Time(b, format='mjd').datetime for b in bin_centers]
            bin_centers = [pd.Timestamp(b) for b in bc]
        bd = pd.DataFrame(np.column_stack([bin_centers, bin_means, bin_std, upper, lower]), columns = ['centers','means','std','upper','lower'])

        bd = bd.fillna(np.nan)
        #if self.bin_data is not None:
        #    self.bin_data.data = bd 
        #else:
        return bd

    def obstype_selection(self, attr, old, new):
        otypes = np.array(['ALL','SCIENCE','DARK','ZERO','FLAT','TWILIGHT','OTHER'])
        self.obstype = otypes[new]

    def data_selections(self, data):
        if 'ALL' in self.obstype:
            pass
        else:
            data = data[data.obstype.isin(self.obstype)]
        return data

    def get_data(self, xx, attr1, attr2, other_attr = [],update=False):
        self.xx = xx
        self.other_attr = other_attr
        attr_list = np.hstack([[xx, attr1, attr2],other_attr])
        data = pd.DataFrame(self.data_source.data)
        data = self.data_selections(data)
        data = data[attr_list]
        self.dd = ColumnDataSource(data[[xx, attr1, attr2]])

        data_ = data.rename(columns={attr1:'attr1', attr2:'attr2'}) 
        if update:
            self.plot_source.data = data_
            self.main_plot.xaxis.axis_label = attr1
            self.main_plot.yaxis.axis_label = attr2
            self.ts1.yaxis.axis_label = attr1
            self.ts2.yaxis.axis_label = attr2
            self.main_plot.title.text  = '{} vs {}'.format(attr1, attr2)
            self.ts1.title.text = 'Time vs. {}'.format(attr1)
            self.ts2.title.text = 'Time vs. {}'.format(attr2)
            self.bin_data.data = self.update_binned_data('attr1','attr2', pd.DataFrame(self.plot_source.data))
            self.bin_data1.data = self.update_binned_data(self.xx,'attr1', pd.DataFrame(self.plot_source.data))
            self.bin_data2.data = self.update_binned_data(self.xx,'attr2', pd.DataFrame(self.plot_source.data))
        else:
            self.plot_source = ColumnDataSource(data_)
            self.sel_data = ColumnDataSource(data=dict(attr1=[], attr2=[]))

            self.bin_data = ColumnDataSource(self.update_binned_data('attr1','attr2', pd.DataFrame(self.plot_source.data)))
            self.bin_data1 = ColumnDataSource(self.update_binned_data(self.xx,'attr1', pd.DataFrame(self.plot_source.data)))
            self.bin_data2 = ColumnDataSource(self.update_binned_data(self.xx,'attr2', pd.DataFrame(self.plot_source.data)))

        if self.data_det_option.active == 0:
            self.details.text = 'Data Overview: \n ' + str(pd.DataFrame(self.dd.data).describe())
            self.cov.text = 'Covariance of {} & {}: \n{}'.format(self.x_select.value, self.y_select.value, str(pd.DataFrame(self.dd.data).cov()))

    def figure(self, width=900, height=300, x_axis_label=None, 
                 y_axis_label=None, tooltips=None, title=None):
        if tooltips is None:
            tooltips = self.default_tooltips

        if x_axis_label == 'DATETIME':
            fig = figure(plot_width=width, plot_height=height, 
                        tools=self.tools, tooltips=tooltips, toolbar_location="below",
                        x_axis_label=x_axis_label, y_axis_label=y_axis_label, x_axis_type='datetime', title=title)
        else:
            fig = figure(plot_width=width, plot_height=height, 
                        tools=self.tools, tooltips=tooltips, toolbar_location="below",
                        x_axis_label=x_axis_label, y_axis_label=y_axis_label, title=title)

        fig.hover.show_arrow = True

        return fig

    def corr_plot(self, fig, x, y, source, size=5, selection_color='orange', 
                    alpha=0.75, nonselection_alpha=0.1, selection_alpha=0.5):
        p = fig.circle(x=x, y=y, size=size, source=source, selection_color=selection_color,
                        alpha=alpha, nonselection_alpha=nonselection_alpha,
                        selection_alpha=selection_alpha)
        return p

    def circle_plot(self, fig, x, y, source, size=5, selection_color='orange'):
        p = fig.circle(x=x, y=y, size=size, source=source, selection_color=selection_color)

        return p

    def pos_scatter(self, fig, source, attr, size=5):
        p = fig.circle(x='X', y='Y', size=size, source=source, fill_color={'field': attr})

        return p

    def time_series_plot(self):
        self.main_plot = self.figure(width=450, height=450, tooltips=self.page_tooltips, x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, title='{} vs {}'.format(self.x_select.value, self.y_select.value))
        self.ts1 = self.figure(x_axis_label=self.xx, tooltips=self.page_tooltips, y_axis_label=self.x_select.value, title='Time vs. {}'.format(self.x_select.value))
        self.ts2 = self.figure(x_axis_label=self.xx, tooltips=self.page_tooltips, y_axis_label=self.y_select.value, title='Time vs. {}'.format(self.y_select.value))
        if self.plot_source is not None:
            self.c1 = self.corr_plot(self.main_plot, x='attr1',y='attr2', source=self.plot_source)
            self.c2 = self.main_plot.circle(x='centers',y='means',color='red',source=self.bin_data)
            self.c3 = self.main_plot.varea(x='centers',y1='upper',y2='lower',source=self.bin_data,alpha=0.4,color='red')
            self.c4 = self.circle_plot(self.ts1, x=self.xx,y='attr1',source=self.plot_source)
            self.c5 = self.ts1.circle(x='centers',y='means',color='red',source=self.bin_data1)
            self.c6 = self.ts1.varea(x='centers',y1='upper',y2='lower',source=self.bin_data1,alpha=0.4,color='red')
            self.c7 = self.circle_plot(self.ts2, x=self.xx,y='attr2',source=self.plot_source)
            self.c8 = self.ts2.circle(x='centers',y='means',color='red',source=self.bin_data2)
            self.c9 = self.ts2.varea(x='centers',y1='upper',y2='lower',source=self.bin_data2,alpha=0.4,color='red')


    def bin_plot(self, attr, old, new):
        for page in [self.c1, self.c2, self.c3, self.c4, self.c5, self.c6, self.c7, self.c8, self.c9]:
            page.visible = False
        if 0 in new:
            for page in [self.c1, self.c4, self.c7]:
                page.visible = True
        if 1 in new:
            for page in [self.c2, self.c3, self.c5, self.c6, self.c8, self.c9]:
                page.visible = True

    def update_selected_data(self, attr, old, new):
        data = self.plot_source.data
        selected = pd.DataFrame(data)
        selected = selected.iloc[new,:][['attr1','attr2']]
        self.sel_data.data = selected.rename(columns={'attr1':self.x_select.value, 'attr2':self.y_select.value}) 
        if self.data_det_option.active == 1:
            self.details.text = 'Data Overview: \n ' + str(pd.DataFrame(self.sel_data.data).describe())
            self.cov.text = 'Covariance of {} & {}: \n{}'.format(self.x_select.value, self.y_select.value, str(pd.DataFrame(self.sel_data.data).cov()))
    def plot_binned_data(self):
        self.bin_data.data = self.update_binned_data('attr1','attr2')
        self.bin_data1.data = self.update_binned_data(self.xx, 'attr1')
        self.bin_data2.data = self.update_binned_data(self.xx,'attr2')


    def data_det_type(self, attr, old, new):
        if new == 0:
            self.details.text = 'Data Overview: \n ' + str(pd.DataFrame(self.dd.data).describe())
            self.cov.text = 'Covariance of Option 1 & 2: \n' + str(pd.DataFrame(self.dd.data).cov())
        if new == 1:
            self.details.text = 'Data Overview: \n ' + str(pd.DataFrame(self.sel_data.data).describe())
            self.cov.text = 'Covariance of Option 1 & 2: \n' + str(pd.DataFrame(self.sel_data.data).cov())





