from bokeh.io import curdoc
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select, Slider, CheckboxGroup, ColumnDataSource, RadioGroup
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
from scipy import stats
import pandas as pd 
import numpy as np 
from datetime import datetime
from astropy.time import Time 


class Plots:
    def __init__(self, title, source=None):
        '''
        Args:
            title : 

        OPTIONS:
            source :

        '''
        self.subt_style = {'font-family':'serif', 'font-size':'200%'}
        self.text_style = {'font-family':'serif', 'font-size':'125%'}
        self.title = title
        self.header = Div(text="{}".format(title), width=500, style = self.subt_style)
        self.data_source = source  # Here it will pick up the latest
        self.tools = 'pan,wheel_zoom,lasso_select,reset,undo,save,hover'
        self.bin_slider = Slider(start=1, end = 100, value=100, step=1, title="# of Bins",direction="rtl")

        self.details = PreText(text=' ', width=500)
        self.cov = PreText(text=' ', width=500)

        self.btn = Button(label='Plot', button_type='primary', width=200)
        self.save_btn = Button(label='Save selection', button_type='primary',width=200)

        self.replot_btn = Button(label='Replot',button_type='primary',width=200)
        self.bin_option = CheckboxGroup(labels=["Raw Data","Binned Data"], active=[0])
        self.data_det_option = RadioGroup(labels=["All Data","Selected Data"], active=0)
        self.fp_tooltips = None
        self.bin_data = None

        self.pos_tooltips = [
                    ("fiber","@FIBER"),
                    ("device","@DEVICE_TYPE"),
                    ("location","@LOCATION"),
                    ("(x,y)", "(@X, @Y)"),
                    ("spectro", "@SPECTRO")]

        self.default_tooltips = [
                    ("index", "$index"),
                    ("(x,y)", "($x, $y)")]

    def prepare_layout(self):
        self.x_select = Select(title='Option 1', options=self.x_options)
        self.y_select = Select(title='Option 2', options=self.y_options)

    def update(self):
        self.get_data(self.xx, self.x_select.value, self.y_select.value, self.other_attr, update=True)

    def save_data(self):
        dd = pd.DataFrame(self.sel_data.data)
        dd = dd.rename(columns={'attr1':self.x_select.value, 'attr2':self.y_select.value})
        dd.to_csv('{}_data_selected.csv'.format(datetime.now().strftime('%Y%m%d_%H:%M:%S.%f')),index=False)



    def update_binned_data(self,attr1, attr2):
        data = pd.DataFrame(self.plot_source.data)
        dd = data[pd.notnull(data[attr1])]
        dd = dd[pd.notnull(dd[attr2])]
        x = np.array(dd[attr1])
        y = np.array(dd[attr2])
        
        if attr1 == 'datetime':
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
        if attr1 == 'datetime':
            bc = [Time(b, format='mjd').datetime for b in bin_centers]
            bin_centers = [pd.Timestamp(b) for b in bc]
        bd = pd.DataFrame(np.column_stack([bin_centers, bin_means, bin_std, upper, lower]), columns = ['centers','means','std','upper','lower'])

        bd = bd.fillna(np.nan)
        #if self.bin_data is not None:
        #    self.bin_data.data = bd 
        #else:
        return bd

    def get_data(self, xx, attr1, attr2, other_attr = [],update=False):
        self.xx = xx
        self.other_attr = other_attr
        attr_list = np.hstack([[xx, attr1, attr2],other_attr])
        data = pd.DataFrame(self.data_source.data)[attr_list]
        self.dd = ColumnDataSource(data[[xx, attr1, attr2]])

        data_ = data.rename(columns={attr1:'attr1', attr2:'attr2'}) 
        if update:
            self.plot_source.data = data_
            self.corr.xaxis.axis_label = attr1
            self.corr.yaxis.axis_label = attr2
            self.ts1.yaxis.axis_label = attr1
            self.ts2.yaxis.axis_label = attr2
            self.corr.title.text  = '{} vs {}'.format(attr1, attr2)
            self.ts1.title.text = 'Time vs. {}'.format(attr1)
            self.ts2.title.text = 'Time vs. {}'.format(attr2)
            self.bin_data.data = self.update_binned_data('attr1','attr2')
            self.bin_data1.data = self.update_binned_data(self.xx,'attr1')
            self.bin_data2.data = self.update_binned_data(self.xx,'attr2')
        else:
            self.plot_source = ColumnDataSource(data_)
            self.sel_data = ColumnDataSource(data=dict(attr1=[], attr2=[]))

            self.bin_data = ColumnDataSource(self.update_binned_data('attr1','attr2'))
            self.bin_data1 = ColumnDataSource(self.update_binned_data(self.xx,'attr1'))
            self.bin_data2 = ColumnDataSource(self.update_binned_data(self.xx,'attr2'))

        if self.data_det_option.active == 0:
            self.details.text = 'Data Overview: \n ' + str(pd.DataFrame(self.dd.data).describe())
            self.cov.text = 'Covariance of Option 1 & 2: \n' + str(pd.DataFrame(self.dd.data).cov())




    def figure(self, width=900, height=300, x_axis_label=None, 
                 y_axis_label=None, tooltips=None, title=None):
        if tooltips is None:
            tooltips = self.default_tooltips

        if x_axis_label == 'datetime':
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

    def pos_scatter(self, fig, df, attr, size=5):
        p = fig.circle(x='X', y='Y', size=size, source=df, fill_color={'field': attr})

        return p

    def time_series_plot(self):
        self.corr = self.figure(width=450, height=450, tooltips=self.page_tooltips, x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, title='{} vs {}'.format(self.x_select.value, self.y_select.value))
        self.ts1 = self.figure(x_axis_label=self.xx, tooltips=self.page_tooltips, y_axis_label=self.x_select.value, title='Time vs. {}'.format(self.x_select.value))
        self.ts2 = self.figure(x_axis_label=self.xx, tooltips=self.page_tooltips, y_axis_label=self.y_select.value, title='Time vs. {}'.format(self.y_select.value))
        if self.plot_source is not None:
            self.c1 = self.corr_plot(self.corr, x='attr1',y='attr2', source=self.plot_source)
            self.c2 = self.corr.circle(x='centers',y='means',color='red',source=self.bin_data)
            self.c3 = self.corr.varea(x='centers',y1='upper',y2='lower',source=self.bin_data,alpha=0.4,color='red')
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
            self.cov.text = 'Covariance of Option 1 & 2: \n' + str(pd.DataFrame(self.sel_data.data).cov())

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





