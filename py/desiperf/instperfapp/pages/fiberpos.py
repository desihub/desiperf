
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models.widgets.markups import Div
from bokeh.models import ColumnDataSource, PreText, Select
from bokeh.plotting import figure

from static.page import Page

class FiberPosPage(Page):
	def __init__(self, source=None):
		self.page = Page('Fiber Positioner Accuracy', source)
		self.txt = self.page.text("This is a sentence")
		#self.btn.on_click(self.print_something)
		self.data_source = self.page.data_source

		x_options = ['max_blind','max_blind_95','rms_blind',
		             'rms_blind_95', 'max_corr', 'max_corr_95', 
		             'rms_corr', 'rms_corr_95']
        self.x_select = Select(value='max_blind',options=x_options)
		y_options = ['airmass','dome_az']
		self.y_select = Select(value=y_options[0], options=y_options)


	def page_layout(self):
		this_layout = layout([[self.page.header],
						[self.x_select, self.y_select],
						[self.ts1]])
		tab = Panel(child=this_layout, title=self.page.title)
		return tab

	def time_series_plot():
		self.ts1 = figure(plot_width=900, plot_height=200, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
		self.ts1.line(x_select.value, y_select.value, source=self.data_source)
		self.ts1.circle(x_select.value, y_select.value, size=1, source=self.data_source, color=None, selection_color="orange")


	def update(self):
		self.time_series_plot()

	def run(self):
		self.x_select.on_change(self.update)
		self.y_select.on_change(self.update)