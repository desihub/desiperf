from bokeh.models import Button, CheckboxButtonGroup, PreText, Select, Slider, CheckboxGroup, ColumnDataSource, RadioGroup, CustomJS, Line
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
from scipy import stats
import pandas as pd 
import numpy as np 
from datetime import datetime
from astropy.time import Time 
import matplotlib.dates as mdates

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

        self.plot_trend_option = CheckboxGroup(labels=['Plot Trend Line'])
        self.mp_tl_det = PreText(text=' ',width=300)
        self.ts1_tl_det = PreText(text=' ',width=300)
        self.ts2_tl_det = PreText(text=' ',width=300)

        self.pos_tooltips = [
                    ("fiber","@FIBER"),
                    ("device","@DEVICE_TYPE"),
                    ("location","@LOCATION"),
                    ("(x,y)", "(@X, @Y)"),
                    ("spectro", "@SPECTRO")]

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

    def update(self):
        self.change_btn_label(1)
        self.get_data(self.xx, self.x_select.value, self.y_select.value, self.other_attr, update=True)
        self.change_btn_label(0)

    def save_data(self):
        dd = pd.DataFrame(self.sel_data.data)
        dd = dd.rename(columns={'attr1':self.x_select.value, 'attr2':self.y_select.value})
        dd.to_csv('{}_data_selected.csv'.format(datetime.now().strftime('%Y%m%d_%H:%M:%S.%f')),index=False)


    def update_binned_data(self,attr1, attr2, data):
        data = pd.DataFrame(data)
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

        self.attr_list = np.hstack([[xx, attr1, attr2],other_attr])
        data = pd.DataFrame(self.data_source.data)
        data = self.data_selections(data)
        data = data[self.attr_list]
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

            self.mp_tl_source.data = self.calc_trend_line(self.plot_source.data['attr1'],self.plot_source.data['attr2'])[0]
            self.ts1_tl_source.data = self.calc_trend_line(self.plot_source.data['DATETIME'],self.plot_source.data['attr1'])[0]
            self.ts2_tl_source.data = self.calc_trend_line(self.plot_source.data['DATETIME'],self.plot_source.data['attr2'])[0]

            self.mp_binned_tl_source.data = self.calc_trend_line(self.bin_data.data['centers'],self.bin_data.data['means'])[0]
            self.ts1_binned_tl_source.data = self.calc_trend_line(self.bin_data1.data['centers'],self.bin_data1.data['means'])[0]
            self.ts2_binned_tl_source.data = self.calc_trend_line(self.bin_data2.data['centers'],self.bin_data2.data['means'])[0]

            self.mp_tl_values = self.calc_trend_line(self.plot_source.data['attr1'],self.plot_source.data['attr2'])[1]
            self.ts1_tl_values = self.calc_trend_line(self.plot_source.data['DATETIME'],self.plot_source.data['attr1'])[1]
            self.ts2_tl_values = self.calc_trend_line(self.plot_source.data['DATETIME'],self.plot_source.data['attr2'])[1]

            self.mp_binned_tl_values = self.calc_trend_line(self.bin_data.data['centers'],self.bin_data.data['means'])[1]
            self.ts1_binned_tl_values = self.calc_trend_line(self.bin_data1.data['centers'],self.bin_data1.data['means'])[1]
            self.ts2_binned_tl_values = self.calc_trend_line(self.bin_data2.data['centers'],self.bin_data2.data['means'])[1] 


        else:
            self.plot_source = ColumnDataSource(data_)
            self.sel_data = ColumnDataSource(data=dict(attr1=[], attr2=[]))

            self.bin_data = ColumnDataSource(self.update_binned_data('attr1','attr2', pd.DataFrame(self.plot_source.data)))
            self.bin_data1 = ColumnDataSource(self.update_binned_data(self.xx,'attr1', pd.DataFrame(self.plot_source.data)))
            self.bin_data2 = ColumnDataSource(self.update_binned_data(self.xx,'attr2', pd.DataFrame(self.plot_source.data)))

            self.mp_tl_source = ColumnDataSource(self.calc_trend_line(self.plot_source.data['attr1'],self.plot_source.data['attr2'])[0])
            self.ts1_tl_source = ColumnDataSource(self.calc_trend_line(self.plot_source.data['DATETIME'],self.plot_source.data['attr1'])[0])
            self.ts2_tl_source = ColumnDataSource(self.calc_trend_line(self.plot_source.data['DATETIME'],self.plot_source.data['attr2'])[0])

            self.mp_binned_tl_source = ColumnDataSource(self.calc_trend_line(self.bin_data.data['centers'],self.bin_data.data['means'])[0])
            self.ts1_binned_tl_source = ColumnDataSource(self.calc_trend_line(self.bin_data1.data['centers'],self.bin_data1.data['means'])[0])
            self.ts2_binned_tl_source = ColumnDataSource(self.calc_trend_line(self.bin_data2.data['centers'],self.bin_data2.data['means'])[0])

            self.mp_tl_values = self.calc_trend_line(self.plot_source.data['attr1'],self.plot_source.data['attr2'])[1]
            self.ts1_tl_values = self.calc_trend_line(self.plot_source.data['DATETIME'],self.plot_source.data['attr1'])[1]
            self.ts2_tl_values = self.calc_trend_line(self.plot_source.data['DATETIME'],self.plot_source.data['attr2'])[1]

            self.mp_binned_tl_values = self.calc_trend_line(self.bin_data.data['centers'],self.bin_data.data['means'])[1]
            self.ts1_binned_tl_values = self.calc_trend_line(self.bin_data1.data['centers'],self.bin_data1.data['means'])[1]
            self.ts2_binned_tl_values = self.calc_trend_line(self.bin_data2.data['centers'],self.bin_data2.data['means'])[1]  

        if self.data_det_option.active == 0:
            self.details.text = 'Data Overview: \n ' + str(pd.DataFrame(self.dd.data).describe())
            self.cov.text = 'Covariance of {} & {}: \n{}'.format(self.x_select.value, self.y_select.value, str(pd.DataFrame(self.dd.data).cov()))


        if self.plot_trend_option.active == [0]:
        	if self.bin_option.active == [0]:
        		self.mp_tl_det.text = self.attr_list[1] + ' Vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.mp_tl_values[0]) + ' Y-Int: ' + np.str(self.mp_tl_values[1])
        		self.ts1_tl_det.text = 'Time Vs. ' + self.attr_list[1] + '\nSlope: ' + np.str(self.ts1_tl_values[0]) + ' Y-Int: ' + np.str(self.ts1_tl_values[1])
        		self.ts2_tl_det.text = 'Time Vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.ts2_tl_values[0]) + ' Y-Int: ' + np.str(self.ts2_tl_values[1])
        	elif self.bin_option.active == [0,1] or self.bin_option.active == [1]:
        		self.mp_tl_det.text = self.attr_list[1] + ' Vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.mp_binned_tl_values[0]) + ' Y-Int: ' + np.str(self.mp_binned_tl_values[1])
        		self.ts1_tl_det.text = 'Time Vs. ' + self.attr_list[1] + '\nSlope: ' + np.str(self.ts1_binned_tl_values[0]) + ' Y-Int: ' + np.str(self.ts1_binned_tl_values[1])
        		self.ts2_tl_det.text = 'Time Vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.ts2_binned_tl_values[0]) + ' Y-Int: ' + np.str(self.ts2_binned_tl_values[1])       		
        	elif self.bin_option.active == []:
        		self.mp_tl_det.text = self.attr_list[1] + ' Vs. ' + self.attr_list[2] + '\nSlope: NA Y-Int: NA'
        		self.ts1_tl_det.text = 'Time Vs. ' + self.attr_list[1] + '\nSlope: NA Y-Int: NA'
        		self.ts2_tl_det.text = 'Time Vs. ' + self.attr_list[2] + '\nSlope: NA Y-Int: NA'
       	elif self.plot_trend_option.active == []:
       		self.mp_tl_det.text = self.attr_list[1] + ' Vs. ' + self.attr_list[2] + '\nSlope: NA Y-Int: NA'
        	self.ts1_tl_det.text = 'Time Vs. ' + self.attr_list[1] + '\nSlope: NA Y-Int: NA'
        	self.ts2_tl_det.text = 'Time Vs. ' + self.attr_list[2] + '\nSlope: NA Y-Int: NA'

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
 
            self.l1 = self.main_plot.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.mp_tl_source)
            self.l2 = self.ts1.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.ts1_tl_source)
            self.l3 = self.ts2.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.ts2_tl_source)
            self.l4 = self.main_plot.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.mp_binned_tl_source)
            self.l5 = self.ts1.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.ts1_binned_tl_source)
            self.l6 = self.ts2.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.ts2_binned_tl_source)

            for page in [self.l1,self.l2,self.l3,self.l4,self.l5,self.l6]:
            	page.visible = False

        self.bin_plot('new',[0],[0])


    def bin_plot(self, attr, old, new):
        for page in [self.c1, self.c2, self.c3, self.c4, self.c5, self.c6, self.c7, self.c8, self.c9]:
            page.visible = False
        if 0 in new:
        	for page in [self.c1, self.c4, self.c7]:
        		page.visible = True
        		if self.plot_trend_option.active == [0]:
        			for line in [self.l1,self.l2,self.l3]:
        				line.visible  = True
        			for line in [self.l4,self.l5,self.l6]:
        				line.visible = False
        			self.mp_tl_det.text = self.attr_list[1] + ' Vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.mp_tl_values[0]) + ' Y-Int: ' + np.str(self.mp_tl_values[1])
        			self.ts1_tl_det.text = 'Time Vs. ' + self.attr_list[1] + '\nSlope: ' + np.str(self.ts1_tl_values[0]) + ' Y-Int: ' + np.str(self.ts1_tl_values[1])
        			self.ts2_tl_det.text = 'Time Vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.ts2_tl_values[0]) + ' Y-Int: ' + np.str(self.ts2_tl_values[1])
        if 1 in new:
        	for page in [self.c2, self.c3, self.c5, self.c6, self.c8, self.c9]:
        		page.visible = True
        		if self.plot_trend_option.active == [0]:
        			for line in [self.l1,self.l2,self.l3]:
        				line.visible = False
        			for line in [self.l4,self.l5,self.l6]:
        				line.visible = True
        			self.mp_tl_det.text = self.attr_list[1] + ' Vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.mp_binned_tl_values[0]) + ' Y-Int: ' + np.str(self.mp_binned_tl_values[1])
        			self.ts1_tl_det.text = 'Time Vs. ' + self.attr_list[1] + '\nSlope: ' + np.str(self.ts1_binned_tl_values[0]) + ' Y-Int: ' + np.str(self.ts1_binned_tl_values[1])
        			self.ts2_tl_det.text = 'Time Vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.ts2_binned_tl_values[0]) + ' Y-Int: ' + np.str(self.ts2_binned_tl_values[1])

    def update_selected_data(self, attr, old, new):
        data = self.plot_source.data
        selected = pd.DataFrame(data)
        selected = selected.iloc[new,:][['attr1','attr2']]
        self.sel_data.data = selected.rename(columns={'attr1':self.x_select.value, 'attr2':self.y_select.value}) 
        if self.data_det_option.active == 1:
            self.details.text = 'Data Overview: \n ' + str(pd.DataFrame(self.sel_data.data).describe())
            self.cov.text = 'Covariance of {} & {}: \n{}'.format(self.x_select.value, self.y_select.value, str(pd.DataFrame(self.sel_data.data).cov()))
    def plot_binned_data(self):
        self.bin_data.data = self.update_binned_data('attr1','attr2', pd.DataFrame(self.plot_source.data))
        self.bin_data1.data = self.update_binned_data(self.xx, 'attr1', pd.DataFrame(self.plot_source.data))
        self.bin_data2.data = self.update_binned_data(self.xx,'attr2', pd.DataFrame(self.plot_source.data))

        for page in [self.l1,self.l2,self.l3,self.l4,self.l5,self.l6]:
        	page.visible = False

        if self.plot_trend_option.active == [0]:
        	self.l4 = self.main_plot.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.mp_binned_tl_source)
        	self.l5 = self.ts1.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.ts1_binned_tl_source)
        	self.l6 = self.ts2.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.ts2_binned_tl_source)

    def data_det_type(self, attr, old, new):
        if new == 0:
            self.details.text = 'Data Overview: \n ' + str(pd.DataFrame(self.dd.data).describe())
            self.cov.text = 'Covariance of Option 1 & 2: \n' + str(pd.DataFrame(self.dd.data).cov())
        if new == 1:
            self.details.text = 'Data Overview: \n ' + str(pd.DataFrame(self.sel_data.data).describe())
            self.cov.text = 'Covariance of Option 1 & 2: \n' + str(pd.DataFrame(self.sel_data.data).cov())

    def calc_trend_line(self,x_attr,y_attr):
    	df = pd.DataFrame(data = dict(attr1 = x_attr,attr2 = y_attr))
    	df = df.dropna(thresh=2)

    	try:
    		x = mdates.date2num(df['attr1'])
    	except:
    		x = df['attr1']

    	try:
    		y = mdates.date2num(df['attr2'])
    	except:
    		y = df['attr2']

    	trend = np.polyfit(x,y,1,full=True)
    	predicted = [trend[0][0]*i + trend[0][1] for i in x]
    	slope = np.float("{:.2e}".format(trend[0][0]))
    	y_int = np.float("{:.2e}".format(trend[0][1]))

    	return pd.DataFrame(data=dict(attr=df['attr1'],trend_line=predicted)), [slope, y_int]

    def plot_trend_line(self, attr, old, new):
    	for page in [self.l1,self.l2,self.l3,self.l4,self.l5,self.l6]:
    		page.visible = False
    	self.mp_tl_det.text = self.attr_list[1] + ' Vs. ' + self.attr_list[2] + '\nSlope: NA Y-Int: NA'
    	self.ts1_tl_det.text = 'Time Vs. ' + self.attr_list[1] + '\nSlope: NA Y-Int: NA'
    	self.ts2_tl_det.text = 'Time Vs. ' + self.attr_list[2] + '\nSlope: NA Y-Int: NA'
    	if 0 in new:
    		if self.bin_option.active == [0]:
    			for page in [self.l1,self.l2,self.l3]:
    				page.visible = True
    			self.mp_tl_det.text = self.attr_list[1] + ' Vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.mp_tl_values[0]) + ' Y-Int: ' + np.str(self.mp_tl_values[1])
    			self.ts1_tl_det.text = 'Time Vs. ' + self.attr_list[1] + '\nSlope: ' + np.str(self.ts1_tl_values[0]) + ' Y-Int: ' + np.str(self.ts1_tl_values[1])
    			self.ts2_tl_det.text = 'Time Vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.ts2_tl_values[0]) + ' Y-Int: ' + np.str(self.ts2_tl_values[1])	
    		if self.bin_option.active == [0,1] or self.bin_option.active == [1]:
    			for page in [self.l4,self.l5,self.l6]:
    				page.visible = True
    			self.mp_tl_det.text = self.attr_list[1] + ' Vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.mp_binned_tl_values[0]) + ' Y-Int: ' + np.str(self.mp_binned_tl_values[1])
    			self.ts1_tl_det.text = 'Time Vs. ' + self.attr_list[1] + '\nSlope: ' + np.str(self.ts1_binned_tl_values[0]) + ' Y-Int: ' + np.str(self.ts1_binned_tl_values[1])

    			self.ts2_tl_det.text = 'Time Vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.ts2_binned_tl_values[0]) + ' Y-Int: ' + np.str(self.ts2_binned_tl_values[1])

    def change_btn_label(self,a):
        if a == 0:
            self.btn.label = 'Re-Plot'
        elif a == 1:
            self.btn.label = 'Plotting ... Please Wait'

    def activate_buttons(self):
        self.btn.on_click(self.update)
        self.bin_option.on_change('active',self.bin_plot)
        self.obstype_option.on_change('active',self.obstype_selection)
        self.save_btn.on_click(self.save_data)
        self.data_det_option.on_change('active',self.data_det_type)
        self.plot_source.selected.on_change('indices', self.update_selected_data)
        self.plot_trend_option.on_change('active',self.plot_trend_line)