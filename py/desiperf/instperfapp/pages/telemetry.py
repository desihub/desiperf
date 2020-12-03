
from bokeh.layouts import column, layout, row, gridplot
from bokeh.models.widgets import Panel
from bokeh.models import CustomJS, ColumnDataSource, Select, Slider, CheckboxGroup
from bokeh.models import ColumnDataSource, DataTable, DateFormatter, TableColumn

from bokeh.models import Button, PreText, Select
from bokeh.models.widgets.markups import Div
from bokeh.plotting import figure
import pandas as pd
import numpy as np 
from datetime import datetime

from static.plots import Plots
from static.page import Page
from static.attributes import Focalplane_attributes
from scipy import stats

import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials


class TelemetryPage(Page):
    def __init__(self, datahandler):
        Page.__init__(self,'Telemetry', source=datahandler.focalplane_source)
        self.page_name = 'telem'

        desc = """ This is a description of all the telemetry used. This is updated at https://docs.google.com/spreadsheets/d/1pMsU5PXhpTyj76vPTfCgBde8jpz04JcXxvOVJVZfLiM/edit#gid=0
            """
        self.description = Div(text=desc, width=800, css_classes=['inst-style'])

        self.url = "https://docs.google.com/spreadsheets/d/1pMsU5PXhpTyj76vPTfCgBde8jpz04JcXxvOVJVZfLiM/edit#gid=0"
        self.credentials = "instperfapp/data/google_access_account.json"
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_url(self.url).sheet1
        self.df = get_as_dataframe(self.sheet, usecols = [0,1,2,3,4], header = 0)
        self.df = self.df.dropna(thresh=1)
        self.source = ColumnDataSource(self.df)

        self.columns = [
            TableColumn(field="Category", title='Category'),
            TableColumn(field="Attribute", title='Attribute'),
            TableColumn(field="Table Location", title="Location"),
            TableColumn(field='Units', title='Units'),
            TableColumn(field='Notes', title='Notes')]

    def page_layout(self):
        this_layout = layout([[self.header],
                              [self.description],
                              [self.data_table]])
        tab = Panel(child=this_layout, title=self.title)
        return tab

    def run(self):
        #Layout
        self.data_table = DataTable(source = self.source, columns = self.columns, width=1000, height=2000)

