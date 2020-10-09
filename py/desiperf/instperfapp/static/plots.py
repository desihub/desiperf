from bokeh.models import Button, CheckboxButtonGroup, PreText, Select, Slider, CheckboxGroup, ColumnDataSource, RadioGroup, CustomJS, Line, HoverTool
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

        self.plot_trend_option = CheckboxGroup(labels=['Plot Trend Line'])
        self.mp_tl_det = PreText(text=' ',width=300)
        self.ts1_tl_det = PreText(text=' ',width=300)
        self.ts2_tl_det = PreText(text=' ',width=300)

        self.bin_data = None
        self.plot_source = None
        self.blue_source = None
        self.red_source = None 
        self.zed_source = None

        self.tools = 'pan,wheel_zoom,lasso_select,reset,undo,save,hover'

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

        return bd

    def get_data(self, xx, attr1, attr2, other_attr = [], update=False):
        self.xx = xx
        self.other_attr = other_attr
        self.attr_list = np.hstack([[xx, attr1, attr2], other_attr])

        if self.page_name == 'pos':
            dd = []
            for f in self.pos_files:
                try:
                    dd.append(pd.read_csv(f))
                except:
                    pass

            data = pd.concat(dd)
            data = self.DH.get_datetime(data)
            data['air_mirror_temp_diff'] = np.abs(data['air_temp'] - data['mirror_temp'])
            data.columns = [x.upper() for x in data.columns]
            data = data[pd.notnull(data['DATETIME'])]

        if self.page_name == 'fp':
            data = pd.DataFrame(self.data_source.data)
            data = self.data_selections(data)


        data = data[self.attr_list]
        self.dd = ColumnDataSource(data[[xx, attr1, attr2]])
        data_ = data.rename(columns={attr1:'attr1', attr2:'attr2'})     

        if update:
            self.plot_source.data = data_
            self.ts0.xaxis.axis_label = attr1
            self.ts0.yaxis.axis_label = attr2
            self.ts1.yaxis.axis_label = attr1
            self.ts2.yaxis.axis_label = attr2
            self.ts0.title.text  = '{} vs {}'.format(attr1, attr2)
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

            if self.page_name == 'pos':
                fp = self.DH.fiberpos
                fp['COLOR'] = 'white'
                fp.at[self.index, 'COLOR'] = 'red'
                self.fp_source.data = fp


        else:
            if self.page_name == 'pos':
                fp = self.DH.fiberpos
                fp['COLOR'] = 'white'
                fp.at[self.index, 'COLOR'] = 'red'
                self.fp_source = ColumnDataSource(fp)

            self.plot_source = ColumnDataSource(data_)
            self.sel_data = ColumnDataSource(data=dict(attr1=[], attr2=[]))

            self.bin_data = ColumnDataSource(self.update_binned_data('attr1','attr2', pd.DataFrame(self.plot_source.data)))
            self.bin_data1 = ColumnDataSource(self.update_binned_data('DATETIME','attr1', pd.DataFrame(self.plot_source.data)))
            self.bin_data2 = ColumnDataSource(self.update_binned_data('DATETIME','attr2', pd.DataFrame(self.plot_source.data)))

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


    def pos_loc_plot(self):
        self.scatt = figure(width=550, height=450, x_axis_label='obsX / mm', y_axis_label='obsY / mm', tooltips=self.pos_tooltips)
        self.scatt.circle(x='X', y='Y', size=5, source=self.fp_source, fill_color={'field': 'COLOR'})


    def time_series_plot(self):

        hover = HoverTool(tooltips=self.page_tooltips, formatters={"@DATETIME":"datetime"}, names=["main",'blue','red','zed'], mode='vline')

        if self.page_name in ['fp','pos']:
            self.ts0 = figure(width=550, height=450, x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, tools=self.tools, title='{} vs {}'.format(self.x_select.value, self.y_select.value))
            self.ts1 = figure(width=900, height=300, x_axis_label=self.xx, y_axis_label=self.x_select.value, x_axis_type='datetime', tools=self.tools, title='Time vs. {}'.format(self.x_select.value))
            self.ts2 = figure(width=900, height=300, x_axis_label=self.xx, y_axis_label=self.y_select.value, x_axis_type='datetime', tools=self.tools, title='Time vs. {}'.format(self.y_select.value))
            self.c1 = self.ts0.circle(x='attr1', y='attr2', source=self.plot_source, size=5, name='main', selection_color='orange', alpha=0.75, nonselection_alpha=0.1, selection_alpha=0.5)
            self.c4 = self.ts1.circle(x=self.xx, y='attr1', size=5, source=self.plot_source, selection_color='orange')
            self.c7 = self.ts2.circle(x=self.xx, y='attr1', size=5, source=self.plot_source, selection_color='orange')

            self.l1 = self.ts0.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.mp_tl_source)
            self.l2 = self.ts1.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.ts1_tl_source)
            self.l3 = self.ts2.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.ts2_tl_source)
            self.l4 = self.ts0.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.mp_binned_tl_source)
            self.l5 = self.ts1.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.ts1_binned_tl_source)
            self.l6 = self.ts2.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.ts2_binned_tl_source)

            for page in [self.l1,self.l2,self.l3,self.l4,self.l5,self.l6]:
                page.visible = False

            if self.x_select.value == 'DATETIME':
                self.ts0.xaxis.axistype = 'datetime'

        elif self.page_name == 'spec':
            self.ts0 = figure(plot_width=1000, plot_height=300, x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, tools=self.tools, title='Blue Detectors')
            self.ts1 = figure(plot_width=1000, plot_height=300, x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, tools=self.tools, title='Red Detectors')
            self.ts2 = figure(plot_width=1000, plot_height=300, x_axis_label=self.x_select.value, y_axis_label=self.y_select.value, tools=self.tools, title='Infrared Detectors')
            self.c1 = self.ts0.circle(x='attrbx', y='attrby', size=5, source=self.blue_source, name='blue', selection_color='orange', color='color', legend='AMP')
            self.c4 = self.ts1.circle(x='attrrx', y='attrry', size=5, source=self.red_source, name='red', selection_color='orange', color='color', legend='AMP') 
            self.c7 = self.ts2.circle(x='attrzx', y='attrzy', size=5, source=self.zed_source, name='zed', selection_color='orange', color='color', legend='AMP') 

            if self.x_select.value == 'DATETIME':
                self.ts0.xaxis.axistype = 'datetime'
                self.ts1.xaxis.axistype = 'datetime'
                self.ts2.xaxis.axistype = 'datetime'


            for p in [self.ts0, self.ts1, self.ts2]:
                p.legend.title = "Amp"
                p.legend.location = "top_right"
                p.legend.orientation = "horizontal" 

        self.ts0.add_tools(hover)
        self.ts1.add_tools(hover)
        self.ts2.add_tools(hover)

        self.c2 = self.ts0.circle(x='centers',y='means',color='red',source=self.bin_data)
        self.c3 = self.ts0.varea(x='centers',y1='upper',y2='lower',source=self.bin_data,alpha=0.4,color='red')
        self.c5 = self.ts1.circle(x='centers',y='means',color='red',source=self.bin_data1)
        self.c6 = self.ts1.varea(x='centers',y1='upper',y2='lower',source=self.bin_data1,alpha=0.4,color='red')
        self.c8 = self.ts2.circle(x='centers',y='means',color='red',source=self.bin_data2)
        self.c9 = self.ts2.varea(x='centers',y1='upper',y2='lower',source=self.bin_data2,alpha=0.4,color='red')

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
        			self.mp_tl_det.text = self.attr_list[1] + ' vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.mp_tl_values[0]) + ' Y-Int: ' + np.str(self.mp_tl_values[1])
        			self.ts1_tl_det.text = 'Time vs. ' + self.attr_list[1] + '\nSlope: ' + np.str(self.ts1_tl_values[0]) + ' Y-Int: ' + np.str(self.ts1_tl_values[1])
        			self.ts2_tl_det.text = 'Time vs. ' + self.attr_list[2] + '\nSlope: ' + np.str(self.ts2_tl_values[0]) + ' Y-Int: ' + np.str(self.ts2_tl_values[1])
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
        	self.l4 = self.ts0.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.mp_binned_tl_source)
        	self.l5 = self.ts1.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.ts1_binned_tl_source)
        	self.l6 = self.ts2.line(x='attr',y='trend_line',line_width=2,line_alpha=0.4,line_color='black',source=self.ts2_binned_tl_source)


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

    