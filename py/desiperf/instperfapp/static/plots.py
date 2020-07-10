from bokeh.io import curdoc
from bokeh.models import Button, CheckboxButtonGroup, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure


class Plots(object):
    def __init__(self, title, source=None):
        self.title = title
        self.header = Div(text="{}".format(title), width=500)
        self.data_source = source  # Here it will pick up the latest
        self.tools = 'pan,wheel_zoom,lasso_select,reset,undo,save,hover'
        self.TOOLTIPS = [
                    ("index", "$index"),
                    ("(x,y)", "($x, $y)"),
                    ("desc", "@desc"),
                    ]

    def update_data(self, source):
        self.data_source = source

    def figure(self, width=900, height=200, x_axis_label=None, y_axis_label=None):
        fig = figure(plot_width=width, plot_height=height, 
                    tools=self.tools, tooltips=self.TOOLTIPS, 
                    x_axis_label=x_axis_label, y_axis_label=y_axis_label)
        fig.hover.show_arrow = True

        return fig

    def corr_plot(self, fig, x, y, source, size=2, selection_color='orange', 
                    alpha=0.75, nonselection_alpha=0.1, selection_alpha=0.5):
        p = fig.circle(x=x, y=y, size=size, source=source, selection_color=selection_color,
                        alpha=alpha, nonselection_alpha=nonselection_alpha,
                        selection_alpha=selection_alpha)
        return p

    def circle_plot(self, fig, x, y, source, size=5, color='blue', selection_color='orange'):
        p = fig.circle(x=x, y=y, size=size, source=source, color=color, selection_color=selection_color)

        return p

    def pos_scatter(self, fig, df, attr, size=5):
        p = fig.circle(x='X', y='Y', size=size, source=df, fill_color={'field': attr})

        return p