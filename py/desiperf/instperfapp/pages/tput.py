
from bokeh.layouts import column, layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource, Select, CustomJS
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
import pandas as pd


from static.plots import Plots

class TputPage(Plots):
    def __init__(self, datahandler):
        Plots.__init__(self,'Throughput Performance', source=datahandler.etc_source)
        self.description = Div(text='These plots show the throughput over time.', width=800, style=self.text_style)

        self.default_options = ['expid', 'estimated_snr', 'goal_snr', 'seeing', 'transparency', 'skylevel', 'max_exposure_time']


    def page_layout(self):
        this_layout = layout([[self.header],
                              [self.description],
                              [self.x_select, self.y_select, self.btn],
                              [self.bin_option, self.save_btn],
                              [self.bin_slider, self.replot_btn],
                              [self.corr, self.details, self.cov],
                              [self.ts1],
                              [self.ts2]])
        tab = Panel(child=this_layout, title=self.title)
        return tab

    def run(self):
        self.x_options = self.default_options
        self.y_options = self.default_options 
        self.prepare_layout()
        self.x_select.value = 'seeing'
        self.y_select.value = 'transparency'
        self.get_data('expid',self.x_select.value, self.y_select.value)

        self.page_tooltips = [
            ("{}".format(self.x_select.value),"@attr1"),
            ("{}".format(self.y_select.value),"@attr2"),
            ("(x,y)", "($x, $y)")]
        self.time_series_plot()
        self.bin_plot('new',[0],[0])
        self.btn.on_click(self.update)
        self.replot_btn.on_click(self.update_binned_data)
        self.bin_option.on_change('active',self.bin_plot)
        self.save_btn.on_click(self.save_data)
        self.plot_source.selected.js_on_change('indices', CustomJS(args=dict(s1=self.plot_source, s2=self.sel_data), code="""
                                                var inds = cb_obj.indices;
                                                var d1 = s1.data;
                                                var d2 = s2.data;
                                                d2['attr1'] = []
                                                d2['attr2'] = []
                                                for (var i = 0; i < inds.length; i++) {
                                                    d2['attr1'].push(d1['attr1'][inds[i]])
                                                    d2['attr2'].push(d1['attr2'][inds[i]])
                                                }
                                                s2.change.emit();
                                                s2.data = d2 """))
