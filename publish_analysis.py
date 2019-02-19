import json
import pandas as pd
from api_client import APIclient
from bokeh.io import show, output_file
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.transform import jitter

output_file("publish_analysis.html")


def get_publish_table():
    api_client = APIclient()
    res = api_client.fetch({}, {'_id': 0, 'section_name': 1, 'pub_date': 1})
    res['pub_date'] = pd.to_datetime(res['pub_date'], format='%H:%M:%S').dt.time
    res.to_pickle('section_names_publish.pkl')

# get_publish_table()
# with open('section_names_publish.pkl', 'wb') as f:
#     pickle.dump(get_publish_table(), f)


df = pd.read_pickle('section_names_publish.pkl')
with open('controls.json') as f:
    cats = json.load(f)['section_name']

source = ColumnDataSource(df)
p = figure(plot_width=900, plot_height=1000, y_range=cats, x_axis_type='datetime')
p.circle(x='pub_date', y=jitter('section_name', width=0.2, range=p.y_range), source=source, alpha=0.3)
p.xaxis[0].formatter.days = ['%Hh']
p.x_range.range_padding = 0
p.ygrid.grid_line_color = None
show(p)
