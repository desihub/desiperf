
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select
from bokeh.models.widgets.markups import Div

from static.plots import Plots

class TputPage():
	def __init__(self, datahandler):
		self.plots = Plots('Throughput Performance', source=datahandler.etc_source)
		self.btn = Button(label='OK', button_type='primary',width=200)
		self.txt = PreText(text="This is a sentence")
		self.data_source = self.plots.data_source


	def page_layout(self):
		this_layout = layout([[self.plots.header],
						[self.btn],
						[self.txt]])
		tab = Panel(child=this_layout, title=self.plots.title)
		return tab

	def ps(self):
		self.txt.text = "This is a new sentence"

	def run(self):
		self.btn.on_click(self.ps)
