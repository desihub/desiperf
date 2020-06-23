from bokeh.io import curdoc
import bokeh.plotting as bk 
from bokeh.models import (LinearColorMapper, ColorBar, ColumnDataSource,
    Title, Button, CheckboxButtonGroup)
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models.widgets.markups import Div
import numpy as np
import pandas as pd 

class Page(object):
	def __init__(self, title, source):
		self.title = title
		self.header = Div(text="{}".format(title), width=500)
		self.data_source = source #Here it will pick up the latest 
		self.tools = 'pan,wheel_zoom,xbox_select,reset'

	def update_data(self, source):
		self.data_source = source

	def button(self,label):
		btn = Button(label=label,button_type='primary',width=300)
		return btn 

	def text(self, text):
		txt = Div(text=text, width=500)
		return txt