import json
from bokeh.plotting import figure
from bokeh.layouts import layout, column
from bokeh.models import ColumnDataSource, FactorRange
from bokeh.models.widgets import Slider, Select, TextInput
from bokeh.io import curdoc
from bokeh.transform import jitter
from api_client import APIclient
import pandas as pd
import datetime

api_client = APIclient()

with open('controls.json') as f:
    ctrls = json.load(f)

year = Slider(title="Year", start=1990, end=2019, value=2019, step=1)
headline = TextInput(title="Headline contains")
# keywords = TextInput(title="Keywords contains")
x_axis = Select(title="X Axis", options=sorted(ctrls['axis']), value="pub_date")
y_axis = Select(title="Y Axis", options=sorted(ctrls['axis']), value="section_name")


tooltip = [
    # ("Headline", "@headline"),
]

query = {}
projections = {
    'pub_date': 1,
}

source = ColumnDataSource(data=dict(x=[], y=[]))
p = figure(plot_height=1500, plot_width=800, y_range=ctrls['section_name'], x_axis_type="datetime", title="", tooltips=tooltip)
p.circle(x="x", y="y", source=source, size=7, line_color=None)


def headline_contains():
    if headline.value != '':
        reg = ''
        for x in headline.value.strip().split(' '):
            reg += '.*' + x + '.*|'
        query['headline.main'] = {'$regex': reg[:-1]}
    else:
        query.pop('headline.main')


def get_publish_table(cat):
    res = api_client.fetch({'pub_date': {'$lte': datetime.datetime(year.value, 12, 31),
                                         '$gte': datetime.datetime(year.value, 1, 1)}},
                           {'_id': 0, cat: 1, 'pub_date': 1})
    res['pub_date'] = pd.to_datetime(res['pub_date'], format='%H:%M:%S').dt.time
    return res


def update():
    df = get_publish_table(y_axis.value)
    p.y_range.factors = df[y_axis.value].dropna().unique().tolist()
    p.circle(x='x', y=jitter('y', width=0.2, range=p.y_range), source=source, alpha=0.3)
    p.xaxis[0].formatter.days = ['%Hh']
    p.x_range.range_padding = 0
    p.ygrid.grid_line_color = None
    p.xaxis.axis_label = x_axis.value
    p.yaxis.axis_label = y_axis.value
    p.title.text = "%d items selected" % len(df)
    source.data = dict(
        x=df[x_axis.value],
        y=df[y_axis.value],
        # headline=df['headline'],
    )


controls = [year, headline, x_axis, y_axis]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())

sizing_mode = 'fixed'  # 'scale_width' also looks nice
inputs = column(*controls, sizing_mode=sizing_mode)
update()
curdoc().add_root(layout([[inputs, p], ], sizing_mode=sizing_mode))
curdoc().title = "NYT"
