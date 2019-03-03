import time
from bokeh.models import ColumnDataSource, TapTool, OpenURL
from bokeh.layouts import gridplot
from bokeh.plotting import figure, save, output_file
t = time.time()

stories_in_page = 40
files_count = 0

"""
To display your stories, change variable `stories` bellow according to the following:
1. stories must be a LIST OF DATAFRAMES. 
   Each df represents a story. It's rows are the articles that belongs to that story.
2. Each dataframe must have columns of the names - `by`, `pub_date`, `headline`, `url`
"""
from minhash_lsh import MinHashLSH  # comment this when changing source of stories
minhash = MinHashLSH()  # comment this when changing source of stories

stories = minhash.get_similar_stories(2018, 2018)
print('{} stories were found'.format(len(stories)))


def save_stories(grid):
    global files_count
    output_file('stories_{}.html'.format(files_count))
    files_count += 1
    save(gridplot(grid))


TOOLTIPS = """
    <div id="Tooltip">
        <div>
            <span style="font-size: 16px; font-weight: bold;">@headline</span>
        </div>
        <div>
            <span style="font-size: 10px;">Click to the article!</span>
        </div>
    </div>
"""
grid = []
for i, story in enumerate(stories):
    if i and not i % stories_in_page:
        save_stories(grid)
        grid = []
    story['y'] = 1
    p = figure(plot_height=100, plot_width=1200, title=story.iloc[0]['headline'],
               x_axis_type='datetime', tools='tap', tooltips=TOOLTIPS)
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.yaxis.visible = False
    source = ColumnDataSource(story)
    p.square('pub_date', 'y', size=10, source=source, fill_alpha=0.5)
    url = '@url'
    taptool = p.select(type=TapTool)
    taptool.callback = OpenURL(url=url)
    grid.append([p])

save_stories(grid)

print('time took: {}'.format(time.time() - t))
