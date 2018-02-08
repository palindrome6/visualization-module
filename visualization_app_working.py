# imports
from bokeh.io import output_file, show
from bokeh.models import (
GMapPlot, GMapOptions, ColumnDataSource, Circle, Triangle, Range1d, PanTool, WheelZoomTool, HoverTool,
ResetTool, Legend, LegendItem, CheckboxGroup, TapTool, Button, TextInput, LinearColorMapper,
BasicTicker, PrintfTickFormatter, ColorBar, BoxAnnotation, Band, LogColorMapper, FuncTickFormatter,
PrintfTickFormatter, NumeralTickFormatter, LinearAxis, Range1d, Legend)
from bokeh.models.widgets.sliders import DateRangeSlider
from collections import OrderedDict
import bokeh.plotting as bk
import pandas as pd
from datetime import date, datetime
from bokeh.models.callbacks import CustomJS
from bokeh.models.widgets import DateRangeSlider
from bokeh.layouts import layout, widgetbox, column, row
from misc_functions import *
from bokeh.plotting import figure, curdoc
from bokeh.transform import linear_cmap, log_cmap
from elog_visualisations import *
from bokeh.events import Tap
from bokeh.models.glyphs import Rect
from bokeh.models.markers import Square

########################################################################
# read data files and process
########################################################################
df_elog_coor = pd.read_csv('data/coordinates-codes-updated.csv', delimiter=';')
# limited_occ_with_gps_new.csv (replace / with -)
data_cc = pd.read_csv('data/limited_occ_with_gps_time.csv', delimiter=';')
#booster location data
df_booster_out = pd.read_csv('data/Installaties_Eindhoven_out.txt', delimiter=';')
df_booster_in = pd.read_csv('data/Installaties_Eindhoven_in.txt', delimiter=';')

df_data_aggregated = pd.read_csv('data/aggregated_day_total_2_positives.csv')



# get selected attribtes for occurrences
lat=list(data_cc['Latitude'])
lon=list(data_cc['Longitude'])
city=list(data_cc['Address'])
issue=list(data_cc['Hoofdtype Melding'])
user=list(data_cc['Verbruiker Omschr'])
dates=list(data_cc['Datum'])
# dates = convert_to_date(dates)
occur_type = set(issue)
occur_type = list(occur_type)
occur_default = list(range(len(occur_type)))

# get selected attribtes for elog
lat_elog=list(df_elog_coor['Lat'])
lon_elog=list(df_elog_coor['Lon'])
place_elog=list(df_elog_coor['Place'])
location_elog=list(df_elog_coor['Location'])
zipcode_elog=list(df_elog_coor['Zipcode'])
value_elog = return_value_list(locations=location_elog)

booster_lat_out = list(df_booster_out['Lat'])
booster_lon_out = list(df_booster_out['Lon'])
booster_name_out = list(df_booster_out['NAAM'])

booster_lat_in = list(df_booster_in['Lat'])
booster_lon_in = list(df_booster_in['Lon'])
booster_name_in = list(df_booster_in['NAAM'])

########################################################################
# Event Handlers
########################################################################


def plot_radius(lat=[], lon=[], radius=[]):
    """
    This function calcualte plot a circle that represents the radious of the events selected into a map

    Parameters
    ---------------------------------
        lon: longitid of the eLog location
        lat: latitud of the eLog location
        radius: the circle radious in Km

    Return
    ---------------------------------
        events_selected: vector with the Id of the events selected
    """
    radius = [rad*1000 for rad in radius] #Convert to Km
#        df = pd.DataFrame([[lat, lon, radius]], columns = ["latitud", "longitud", 'radius'])
#        source = ColumnDataSource(df)
    print(lat)
    print(lon)
    print(radius)
    source_radius_circle.data['lat_radius'] = lat
    source_radius_circle.data['lon_radius'] = lon
    source_radius_circle.data['rad_radius'] = radius
#        radius_circle = Circle(x="longitud", y="latitud",radius= 'radius',fill_alpha=0.5, line_color='black')
#        radius_circle_glyph = plot.add_glyph(source, radius_circle)

# create filtering function, calls return_value_list() to get new consumption values
def filter_usage(attr,old,new):

    #val1 and val2 are new slider values in timestamps
    # val0 = str(slider.value[0])
    val0 = source_fake.data['value'][0][0]
    val0 = str(val0)
    val0 = str(val0[:-3])
    val0 = date.fromtimestamp(int(val0))
    # val1 = str(slider.value[1])
    val1 = source_fake.data['value'][0][1]
    val1=str(val1)
    val1 = str(val1[:-3])
    val1 = date.fromtimestamp(int(val1))

    # new consumption values for the elog locations
    source_elog.data['value_elog'] = return_value_list(location_elog, str(val0), str(val1))

# Function to filter occurrences based on slider and checkbox selection
def filter_occurrences(attr,old,new):

    #val1 and val2 are new slider values in timestamps
    # val0 = str(slider.value[0])
    val0 = str(slider_events.value[0])
    val0 = val0[:-3]
    val0 = date.fromtimestamp(int(val0))
    val1 = str(slider_events.value[1])
    val1 = val1[:-3]
    val1 = date.fromtimestamp(int(val1))

    # checkbox_group.active gives a list of indices corresponding to options selected using checkbox
    possible_events = [occur_type[i] for i in checkbox_group.active]

    # create new events source to display on map, controlled by slider
    source.data={key:[value for i, value in enumerate(source_original.data[key])
    if convert_to_date(source_original.data["dates"][i])>=val0 and convert_to_date(source_original.data["dates"][i])<=val1
    and source_original.data["issue"][i] in possible_events]
    for key in source_original.data}

def heat_map_stuff(df_heat, data_aggregated_day, rolling):
    source_heat_map_update = ColumnDataSource(data=df_heat.reset_index().fillna('NaN').to_dict(orient="list"))
    source_heat_map.data = source_heat_map_update.data

    source_data_aggregated_day.data = ColumnDataSource(data=data_aggregated_day).data
    source_rolling.data = ColumnDataSource(data=rolling).data
    print('generated...')

def get_new_heat_map_source(location, flag=0):
    data = pre_process_hour_consuption(location)
    df_heat = pd.DataFrame(data.stack(), columns=['rate']).reset_index()

    data_aggregated_day_local, rolling_local = pre_process_total(df_data_aggregated, location, 30)


    if flag == 1:
        return df_heat
    else:
        heat_map_stuff(df_heat, data_aggregated_day_local, rolling_local)

def tap_tool_handler(attr,old,new):
    ind = new['1d']['indices'][0]
    # print(lat_elog[ind])
    # print(lon_elog[ind])
    l1 = []
    l2 = []
    r0 = []
    l1.append(lat_elog[ind])
    l2.append(lon_elog[ind])
    r0.append(float(text_input.value))
    plot_radius(l1, l2, r0)
    print('plotted radius')
    print('location number: ', location_elog[ind])
    get_new_heat_map_source(location_elog[ind], 0)




    #data_cc = select_events(lon_elog[ind], lat_elog[ind], data_cc, text_input.value*1000)

def reset_radius():
    l1 = []
    l2 = []
    r = []
    plot_radius(l1, l2, r)

def change_radius(attr,old,new):
    new_rad = float(text_input.value)*1000
    r = []
    r.append(new_rad)
    source_radius_circle.data['rad_radius'] = r


########################################################################
# Define data sources
########################################################################

# data source for drawing radius circle
source_radius_circle = bk.ColumnDataSource(
    data=dict(
        lat_radius=[],
        lon_radius=[],
        rad_radius=[]
    )
)

# data source for outflow boosters
source_booster_out = bk.ColumnDataSource(
    data=dict(
        booster_lat=booster_lat_out,
        booster_lon=booster_lon_out,
        booster_name=booster_name_out
    )
)

# data source for inflow pumping stations
source_booster_in = bk.ColumnDataSource(
    data=dict(
        booster_lat=booster_lat_in,
        booster_lon=booster_lon_in,
        booster_name=booster_name_in
    )
)


# original data source for elog data
source_elog_original = bk.ColumnDataSource(
    data=dict(
        lat_elog=lat_elog,
        lon_elog=lon_elog,
        place_elog=place_elog,
        location_elog=location_elog,
        zipcode_elog=zipcode_elog,
        value_elog = value_elog
    )
)

# dynamic data source for elog data
source_elog = bk.ColumnDataSource(
    data=dict(
        lat_elog=lat_elog,
        lon_elog=lon_elog,
        place_elog=place_elog,
        location_elog=location_elog,
        zipcode_elog=zipcode_elog,
        value_elog = value_elog
    )
)

# original data source for events data
source_original = bk.ColumnDataSource(
    data=dict(
        lat=lat,
        lon=lon,
        city=city,
        issue=issue,
        dates=dates
    )
)

# dynamic data source for events data
source = bk.ColumnDataSource(
    data=dict(
        lat=lat,
        lon=lon,
        city=city,
        issue=issue,
        dates=dates
    )
)

# dummy data source to trigger real callback
source_fake = ColumnDataSource(data=dict(value=[]))




source_heat_map_misc = bk.ColumnDataSource(
    data=dict(
        date_range_0 = [],
        date_range_1 = [],
        location = [],
        x_range = [],
        y_range = [],
        df_rate_max = []
    )
)
########################################################################
# Define widgets
########################################################################

# slider and callbacks for water usage
slider = DateRangeSlider(start=date(2017, 1, 1), end=date(2017, 12, 31), value=(date(2017, 1, 1), date(2017, 12, 31)), title="Consumption period",
step=1, callback_policy="mouseup")
slider.callback = CustomJS(args=dict(source=source_fake), code="""
    source.data = { value: [cb_obj.value] }
""")

# change fake data source, which in turn triggers filter function to modify the real data
source_fake.on_change('data', filter_usage)

# slider and callbacks for events
slider_events = DateRangeSlider(start=date(2017, 1, 1), end=date(2017, 12, 31), value=(date(2017, 1, 1), date(2017, 12, 31)),
step=1, title="Occurrence period")
slider_events.on_change("value", filter_occurrences)

# checkbox for event type
checkbox_group = CheckboxGroup(
        labels=occur_type, active=occur_default)

checkbox_group.on_change("active", filter_occurrences)

# Button to remove radius feature
button = Button(label="Remove Radius", button_type="success")
button.on_click(reset_radius)

# Text input for radius
text_input = TextInput(value="3", title="Distance in km:")
text_input.on_change('value', change_radius)

########################################################################
# Define map layput
########################################################################

# define maps, options
map_options = GMapOptions(lat=51.4416, lng=5.4697, map_type="terrain", zoom=12)
plot = GMapPlot(x_range=Range1d(), y_range=Range1d(), map_options=map_options)
plot.title.text = "Eindhoven"

# use your api key below
plot.api_key = get_api_key()

########################################################################
# Define glyphs
########################################################################

# triangle glyphs on the map
triangle_event = Triangle(x="lon", y="lat", size=12, fill_color="red", fill_alpha=0.5, line_color=None, name="occurrences")
glyph_triangle = plot.add_glyph(source, triangle_event)

# circle glyphs on the map
circle_elog = Circle(x="lon_elog", y="lat_elog", size=12, fill_color=log_cmap("value_elog",
palette = ['#74a9cf', '#3690c0', '#0570b0', '#045a8d', '#023858'],
low=min(source_elog.data["value_elog"]), high=max(source_elog.data["value_elog"]), nan_color='green'),
fill_alpha=0.5, line_color=None, name="elog_locations")
glyph_circle = plot.add_glyph(source_elog, circle_elog)

circle_radius = Circle(x="lon_radius", y="lat_radius", radius= "rad_radius", fill_alpha=0.5, line_color='black')
glyph_circle_radius = plot.add_glyph(source_radius_circle, circle_radius)

square_out = Square(x="booster_lon", y="booster_lat", size=15, fill_color="brown", line_color=None)
glyph_square_out = plot.add_glyph(source_booster_out, square_out)

square_in = Square(x="booster_lon", y="booster_lat", size=15, fill_color="green", line_color=None)
glyph_square_in = plot.add_glyph(source_booster_in, square_in)

########################################################################
# Other misc tools: hovers, taps, etc
########################################################################


# tools to include on the visualization
plot.add_tools(PanTool(), WheelZoomTool(),
	    ResetTool(), TapTool())

# Hover tool for triangles
triangle_hover = HoverTool(renderers=[glyph_triangle],
                         tooltips=OrderedDict([
                             ("Location", "@city"),
                             ("Date", "@dates"),
                             ("Problem", "@issue")
                         ]))
plot.add_tools(triangle_hover)

# Hover tool for circles
circle_hover = HoverTool(renderers=[glyph_circle],
                         tooltips=OrderedDict([
                             ("Place", "@place_elog"),
                             ("Usage", '@value_elog')
                         ]))
plot.add_tools(circle_hover)

# Hover tool for booster out
booster_out_hover = HoverTool(renderers=[glyph_square_out],
                         tooltips=OrderedDict([
                             ("Location", "@booster_name")
                         ]))
plot.add_tools(booster_out_hover)

# Hover tool for booster in
booster_in_hover = HoverTool(renderers=[glyph_square_in],
                         tooltips=OrderedDict([
                             ("Location", "@booster_name")
                         ]))
plot.add_tools(booster_in_hover)

# Tap tool for elog circles
tap_tool = TapTool(names=['elog_locations'], renderers=[glyph_circle])
glyph_circle.data_source.on_change('selected', tap_tool_handler)

# Add legend
legend = Legend(items=[
    LegendItem(label="elog_locations"   , renderers=[glyph_circle]),
    LegendItem(label="occurrences" , renderers=[glyph_triangle]),
    LegendItem(label="Inflow" , renderers=[glyph_square_in]),
    LegendItem(label="Outflow" , renderers=[glyph_square_out])
], orientation="vertical", click_policy="hide")
plot.add_layout(legend, "center")



########################################################################
# Heat map stuff
#######################################################################

df_heat1 = get_new_heat_map_source(location=1163208, flag=1)
data_aggregated_day, rolling = pre_process_total(df_data_aggregated,1163208, 30)
# source_heat_map = ColumnDataSource(data=df_heat.reset_index().fillna('NaN').to_dict(orient="list"))
source_heat_map = ColumnDataSource(data=df_heat1)
source_data_aggregated_day = ColumnDataSource(data=data_aggregated_day)
source_rolling = ColumnDataSource(data = rolling)
data_cc_filtered = pre_process_cc(data_cc)
source_events = ColumnDataSource(data = data_cc_filtered)
# print(source_heat_map.data)

# import datetime
start = datetime.strptime("2017-01-01", "%Y-%m-%d")
end = datetime.strptime("2017-12-31", "%Y-%m-%d")
dates_list = list(pd.date_range(start = start, end = end).strftime('%Y-%m-%d'))

dates_list = [str(j) for j in dates_list]
print(dates_list)

hour_list = []
for j in range(24):
    hour_list.append(str(j))



colors_heat_map = ['#fff7fb', '#ece7f2', '#d0d1e6', '#a6bddb', '#74a9cf', '#3690c0', '#0570b0', '#045a8d', '#023858']
#     mapper = LinearColorMapper(palette=colors, low=df.rate.min(), high=df.rate.max())
mapper_heat_map = LogColorMapper(palette=colors_heat_map, low= 0, high=10000000)

TOOLS_heat_map = "save,pan ,reset, wheel_zoom"
p_heat_map = figure(title="Water consumption in Log(Liters)",x_axis_type="datetime", x_range = dates_list, y_range = list(reversed(hour_list)), tools=TOOLS_heat_map)

heat_map = p_heat_map.rect(x="date", y="hour", width=1, height=1, source = source_heat_map, fill_color={'field': 'rate', 'transform': mapper_heat_map}, line_color=None)
p_events = p_heat_map.triangle(x = 'date', y = 'Hour', legend= "Events", source = source_events, color = 'color', size = 6)




color_bar = ColorBar(color_mapper=mapper_heat_map, border_line_color=None,label_standoff=12, location=(0, 0))
color_bar.formatter = NumeralTickFormatter(format='0.0')
p_heat_map.add_layout(color_bar, 'right')

heat_map_hover = HoverTool(renderers=[heat_map],
                    tooltips=OrderedDict([('Water Consumption (Liters)', '@rate'),
                                        ('date hour', '@date'),
                                         ('hour', '@hour'),
                                       ]))

events_hover = HoverTool(renderers=[p_events],
        tooltips=OrderedDict([('Event description',
        '@{Hoofdtype Melding}'),
        ]))



p_heat_map.grid.grid_line_color = None
p_heat_map.axis.axis_line_color = None
p_heat_map.axis.major_tick_line_color = None
p_heat_map.xaxis.major_label_text_font_size = '0pt'  # turn off x-axis tick labels
p_heat_map.yaxis.axis_label = 'Hour'
p_heat_map.xaxis.axis_label = 'Days'
p_heat_map.axis.major_label_standoff = 0

p_heat_map.legend.location = "top_left"
p_heat_map.legend.click_policy= "hide"
p_heat_map.add_tools(heat_map_hover)
p_heat_map.add_tools(events_hover)

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
p_outliers = figure(title="Daily water consumptions in million of Liters", x_axis_type="datetime", tools=TOOLS_heat_map, x_range = dates_list)
p_circle = p_outliers.circle(x = 'date', y = 'delta_total', size='s', color= 'c', alpha='a',
              legend= "Consumption in ML", source = source_data_aggregated_day)

p_ub = p_outliers.line(x='date', y='ub', legend='upper_bound (2 sigma)', line_dash = 'dashed', line_width = 4, color = '#984ea3',source = source_rolling)
p_mean = p_outliers.line(x='date', y='y_mean', source = source_rolling, line_dash = 'dashed', line_width = 3, legend='moving_average', color = '#4daf4a')

p_outliers.legend.location = "top_left"
p_outliers.legend.orientation = "horizontal"
p_outliers.legend.click_policy= "hide"
p_outliers.ygrid.band_fill_color = "olive"
p_outliers.ygrid.band_fill_alpha = 0.1
p_outliers.xaxis.axis_label = 'Date'
p_outliers.yaxis.axis_label = 'Million of Liters'
p_outliers.xaxis.major_label_orientation = 3.1416 / 3
p_outliers.x_range = p_heat_map.x_range# Same axes as the heatMap
p_outliers.xaxis.formatter = FuncTickFormatter(code=""" var labels = %s; return labels[tick];""" % dates_list)


circle_hover = HoverTool(renderers=[p_circle],
                    tooltips=OrderedDict([('date', '@date'),
                                          ('Water Consumption (ML)', '@delta_total'),
                                         ]))

p_ub_hover = HoverTool(renderers=[p_ub],
                    tooltips=OrderedDict([('date', '@date'),
                                          ('UpperBound water consumption (ML)', '@ub'),
                                         ]))

p_mean_hover = HoverTool(renderers=[p_mean],
                    tooltips=OrderedDict([('date', '@date'),
                                          ('Mean water consumption (ML)', '@y_mean'),
                                         ]))

p_outliers.add_tools(circle_hover)
p_outliers.add_tools(p_ub_hover)
p_outliers.add_tools(p_mean_hover)

########################################################################
# Manage layout
########################################################################

row1 = row([slider, slider_events])
column1 = column([checkbox_group, button, text_input])
row2 = row([plot, column1])
heat_map_layout = gridplot([[p_heat_map,None],[p_outliers,None]], plot_width=1200, plot_height=400, toolbar_location = 'left')
layout = column([row1, row2, heat_map_layout])

curdoc().add_root(layout)