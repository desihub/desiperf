
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource, Select
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
import pandas as pd


from static.plots import Plots

class TputPage():
	def __init__(self, datahandler):
		self.plots = Plots('Throughput Performance', source=datahandler.etc_source)
		self.description = Div(text='These plots show the throughput over time.', width=800, style=self.plots.text_style)
		self.details = PreText(text=' ', width=500)
		self.cov = PreText(text=' ', width=500)
		self.data_source = self.plots.data_source
		self.default_options = ['estimated_snr', 'goal_snr', 'seeing', 'transparency', 'skylevel', 'max_exposure_time', 'expid']

		self.x_select = Select(title='Option 1', value='seeing', options=self.default_options)
		self.y_select = Select(title='Option 2', value='transparency', options=self.default_options)
		self.btn = Button(label='OK', button_type='primary',width=200)

	def get_data(self, attr1, attr2, update=False):
		data = pd.DataFrame(self.data_source.data)[['expid', attr1, attr2]]
		self.details.text = str(data.describe())
		self.cov.text = str(data.cov())
		data_ = data.rename(columns={attr1: 'attr1', attr2: 'attr2'})
		if update:
			self.plot_source.data = data_
		else:
			self.plot_source = ColumnDataSource(data_)

	def page_layout(self):
		this_layout = layout([[self.plots.header],
							  [self.description],
							  [self.x_select, self.y_select, self.btn],
							  [self.corr, self.details, self.cov],
							  [self.ts1],
							  [self.ts2]])
		tab = Panel(child=this_layout, title=self.plots.title)
		return tab

	def time_series_plot(self):
		self.corr = self.plots.figure(width=350, height=250, x_axis_label='attr1', y_axis_label='attr2')
		self.ts1 = self.plots.figure(x_axis_label='expid', y_axis_label='attr1')
		self.ts2 = self.plots.figure(x_axis_label='expid', y_axis_label='attr2')
		if self.data_source is not None:
			self.plots.corr_plot(self.corr, x='attr1', y='attr2', source=self.plot_source)
			self.plots.circle_plot(self.ts1, x='expid', y='attr1', source=self.plot_source)
			self.plots.circle_plot(self.ts2, x='expid', y='attr2', source=self.plot_source)
		# self.corr.circle(x='attr1', y='attr2', size=2, source=self.plot_source, selection_color="orange", alpha=0.6, nonselection_alpha=0.1, selection_alpha=0.4)
		# self.ts1.circle(x='mjd_obs', y='attr1', size=5, source=self.plot_source, color="blue", selection_color="orange")
		# self.ts2.circle(x='mjd_obs', y='attr2', size=5, source=self.plot_source, color="blue", selection_color="orange")

	def update(self):
		self.get_data(self.x_select.value, self.y_select.value, update=True)
		self.time_series_plot()

	def run(self):
		self.get_data(self.x_select.value, self.y_select.value)
		self.time_series_plot()
		self.btn.on_click(self.update)
