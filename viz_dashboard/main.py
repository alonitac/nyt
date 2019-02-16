import json
from bokeh.plotting import figure
from bokeh.layouts import layout, column
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Slider, Select, TextInput
from bokeh.io import curdoc
from api_client import APIclient

api_client = APIclient()

with open('controls.json') as f:
    ctrl = json.load(f)

min_year = Slider(title="Start Year", start=1990, end=2019, value=1990, step=1)
max_year = Slider(title="End Year", start=1990, end=2019, value=2019, step=1)
headline = TextInput(title="Headline contains")
keywords = TextInput(title="Keywords contains")
x_axis = Select(title="X Axis", options=sorted(ctrl['axis']), value="pub_date")
y_axis = Select(title="Y Axis", options=sorted(ctrl['axis']), value="news_desk")
source = ColumnDataSource(data=dict(x=[], y=[], headline=[]))

TOOLTIPS = [
    ("Headline", "@headline"),
]

p = figure(plot_height=600, plot_width=700, title="", toolbar_location=None, tooltips=TOOLTIPS)
p.circle(x="x", y="y", source=source, size=7, color="color", line_color=None, fill_alpha="alpha")


def select():
    return None


def update():
    df = select()
    p.xaxis.axis_label = x_axis.value
    p.yaxis.axis_label = y_axis.value
    p.title.text = "%d items selected" % len(df)
    source.data = dict(
        x=df[x_axis.value],
        y=df[y_axis.value],
        title=df["headline"],
    )


controls = [min_year, max_year, headline, keywords, x_axis, y_axis]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())

sizing_mode = 'fixed'  # 'scale_width' also looks nice
inputs = column(*controls, sizing_mode=sizing_mode)
update()
curdoc().add_root(layout([[inputs, p], ], sizing_mode=sizing_mode))
curdoc().title = "NYT"
