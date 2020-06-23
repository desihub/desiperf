
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models.widgets.markups import Div

from static.page import Page

class TputPage(Page):
	def __init__(self, source):
		self.page = Page('Throughput Performance',source)
		self.btn = self.page.button('OK')
		self.txt = self.page.text("This is a sentence")
		self.data_source = self.page.data_source


	def page_layout(self):
		this_layout = layout([[self.page.header],
						[self.btn],
						[self.txt]])
		tab = Panel(child=this_layout, title=self.page.title)
		return tab

	def ps(self):
		self.txt.text = "This is a new sentence"

	def run(self):
		self.btn.on_click(self.ps)
