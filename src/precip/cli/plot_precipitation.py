#!/usr/bin/env python3

import os
from datetime import datetime
import argparse
from precip.plotter_functions import prompt_subplots
from precip.config import START_DATE, END_DATE
from pathlib import Path

# TODO Add proper CITATION for GPM data and Volcano data
PRECIP_DIR = os.getenv('PRECIP_DIR')

EXAMPLE = f"""
Date format: YYYYMMDD

Example:

    plot_precipitation.py Merapi --style bar --roll 30 --bins 3 --log
    plot_precipitation.py Merapi --style strength --period 20190101:20210929
    plot_precipitation.py Merapi --style strength --period 20190101:20210929 --no-show
    plot_precipitation.py Merapi --style strength --period 20190101:20210929 --no-save
    plot_precipitation.py Merapi --style strength --period 20190101:20210929 --outdir test_dir --no-show
    plot_precipitation.py --style strength --lalo 19.5,-156.5 --period 20190101:20210929 --outdir test_dir
    plot_precipitation.py --style annual --start-date 20190101 --end-date 20210929 --latitude 19.5 --longitude -156.5 --roll 10 --bins 2 --add-event 20200929 20210929
    plot_precipitation.py --style strength --lalo 19.5,-156.5 --period 20190101:20210929 --add-event 20200929 20210929 --elnino
    plot_precipitation.py --style map --end-date 20210929 --polygon 'POLYGON((113.4496 -8.0893,113.7452 -8.0893,113.7452 -7.817,113.4496 -7.817,113.4496 -8.0893))'
    plot_precipitation.py --style map --end-date 20210929 --lalo 19.5:20.5,-155.5:-156.5 --vlim -3 3 --colorbar 'RdBu'
    plot_precipitation.py --download
    plot_precipitation.py --download 20190101 20210929 --dir $PRECIP_DIR
    plot_precipitation.py --list
    plot_precipitation.py --check

"""


def create_parser(iargs=None, namespace=None):
    """ Creates command line argument parser object. """

    # parser = argparse.ArgumentParser(
    #     description='Plot precipitation data from GPM dataset for a specific location at a given date range',
    #     formatter_class=argparse.RawTextHelpFormatter,
    #     epilog=EXAMPLE)
    parser = argparse.ArgumentParser(
        description='Plot precipitation data from GPM dataset for a specific location at a given date range',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)

    parser.add_argument('name',
                        nargs='?',
                        type=str,
                        help='Volcano name')
    # parser.add_argument('coordinates', 
    #                     nargs='1',
    #                     help='Volcano name')

    parser.add_argument('--volcano-name',
                        nargs=1,
                        type=str,
                        metavar=('NAME'),
                        help='Name of the volcano')

    parser.add_argument('--style',
                        choices=['daily','weekly','monthly','yearly','map','bar','annual','strength'],
                        help='Choose plot type')
    parser.add_argument('--download',
                        action='store_true',
                        help='Use ssh')
    parser.add_argument('--list',
                        action='store_true',
                        help='List volcanoes')
    parser.add_argument('--check',
                        action='store_true',
                        help='Check if the file is corrupted')
    parser.add_argument('--use-ssh',
                        action='store_true',
                        dest='use_ssh',
                        help='Use ssh')
    parser.add_argument('--parallel',
                        type=int,
                        default=5,
                        help='Number of parallel downloads')

    parser = add_location_arguments(parser)
    parser = add_date_arguments(parser)
    parser = add_plot_parameters_arguments(parser)
    parser = add_map_parameters_arguments(parser)
    parser = add_save_arguments(parser)

    inps = parser.parse_args(iargs, namespace)

    #exit()
    # FA: create_parser has much too much. 
    ############################ POSITIONAL ARGUMENTS ############################

    # FA: using len(inps.positional) looks strange. I would expect this is handled better by argparse?
    # FA: suggest to assign the positional argument to volcano_name in argparse. If the number of positional arguments is zero:  inps.latitude, inps.longitude = get_latitude_longitude(inps)
    # if len(inps.name) == 1:

    #     # FA: this should be in a function
    #     # Unfortunately this can never work if we pass the coordinates since negative numbers are viewed as options
    #     if any(char.isdigit() for char in inps.name):
    #         if 'POLYGON' in inps.name:
    #             inps.latitude, inps.longitude = parse_polygon(inps.name[0])

    #         else:
    #             coordinates = parse_coordinates(inps.name[0])
    #             inps.latitude = parse_coordinates(coordinates[0])
    #             inps.longitude = parse_coordinates(coordinates[1])

    # inps.volcano_name = inps.name
    # Same issue here
    # if len(inps.positional) == 2:
    #     inps.latitude = parse_coordinates(inps.positional[0])

    #     inps.longitude = parse_coordinates(inps.positional[1])

    ###############################################################################
    inps.volcano_name = [inps.name]

    # FA: Assuming that inps.start_date and inps.end_date will be later consider function: inps.start_date, inps.end_date=get_processing_dates(inps)
    if not inps.period:
        inps.start_date = datetime.strptime(inps.start_date, '%Y%m%d').date()

        #End date subject to variations, check for alternatives on config.py
        inps.end_date = datetime.strptime(inps.end_date, '%Y%m%d').date()

    else:
        if ':' in inps.period:
            dates = inps.period.split(':')
        # TODO not sure if this is to be removed
        elif ',' in inps.period:
            dates = inps.period.split(',')

        inps.start_date = datetime.strptime(dates[0], '%Y%m%d').date()
        inps.end_date = datetime.strptime(dates[1], '%Y%m%d').date()

    if not inps.polygon:

        if inps.latitude:
            if len(inps.latitude) == 1:
                inps.latitude = parse_coordinates(inps.latitude[0])

            elif len(inps.latitude) == 2:
                inps.latitude = [float(inps.latitude[0]), float(inps.latitude[1])]

            else:
                parser.error("--latitude requires 1 or 2 arguments")

        if inps.longitude:
            if len(inps.longitude) == 1:
                inps.longitude = parse_coordinates(inps.longitude[0])

            elif len(inps.longitude) == 2:
                inps.longitude = [float(inps.longitude[0]), float(inps.longitude[1])]

            else:
                parser.error("--longitude requires 1 or 2 arguments")

        if inps.lalo:
            coordinates = parse_coordinates(inps.lalo[0])
            inps.latitude = parse_coordinates(coordinates[0])
            inps.longitude = parse_coordinates(coordinates[1])

    else:
            inps.latitude, inps.longitude = parse_polygon(inps.polygon)

    # FA: Not sure why to introduce inps.average = 'W'. You can use use 'if inps.style == 'weekly'' later in the code?
    if inps.style == 'weekly':
        inps.average = 'W'

    elif inps.style == 'monthly':
        inps.average = 'M'

    elif inps.style == 'yearly':
        inps.average = 'Y'

    elif inps.style == 'annual':
        inps.average = 'D'

    elif inps.style == 'map':
        inps.add_event = None
        inps.roll = 1

    if inps.add_event:
        try:
            inps.add_event = tuple(datetime.strptime(date_string, '%Y-%m-%d').date() for date_string in inps.add_event)

        except ValueError:
            try:
                inps.add_event = tuple(datetime.strptime(date_string, '%Y%m%d').date() for date_string in inps.add_event)

            except ValueError:
                msg = 'Date format not valid, it must be in the format YYYYMMDD or YYYY-MM-DD'
                raise ValueError(msg)

    if not inps.bins:
        inps.bins = 4 if inps.bins > 4 else inps.bins

    return inps


def add_date_arguments(parser):
    """Argument parser for the date range of the search."""
    date = parser.add_argument_group('Date range of the search')
    date.add_argument('--start-date',
                        nargs='?',
                        default=START_DATE,
                        metavar='YYYYMMDD',
                        help='Start date of the search, default is %(default)s')
    date.add_argument('--end-date',
                        nargs='?',
                        default=END_DATE,
                        metavar='YYYYMMDD',
                        help='End date of the search, default is %(default)s')
    date.add_argument('--period',
                        nargs='?',
                        metavar='YYYYMMDD:YYYYMMDD, YYYYMMDD,YYYYMMDD',
                        help='Period of the search')

    return parser


def add_location_arguments(parser):
    """Argument pasrser for the location of the volcano or area of interest."""
    location = parser.add_argument_group('Location of the volcano or area of interest')
    location.add_argument('--latitude',
                        nargs='?',
                        metavar=('LATITUDE', 'LATITUDE:LATITUDE'),
                        help='Latitude')
    location.add_argument('--longitude',
                        nargs='?',
                        metavar=('LONGITUDE', 'LONGITUDE:LONGITUDE'),
                        help='Longitude')
    location.add_argument('--lalo',
                        nargs='?',
                        metavar=('LATITUDE,LONGITUDE', 'LATITUDE:LATITUDE, LONGITUDE:LONGITUDE'),
                        help='Latitude and longitude')
    location.add_argument('--polygon',
                        metavar='POLYGON',
                        help='Polygon of the wanted area (Format from ASF Vertex Tool https://search.asf.alaska.edu/#/)')

    return parser


def add_plot_parameters_arguments(parser):
    """Argument parser for the plot parameters."""
    plot_parameters = parser.add_argument_group('Plot parameters')
    plot_parameters.add_argument('--add-event',
                        nargs='*',
                        metavar=('YYYYMMDD, YYYY-MM-DD'),
                        help='Add event to the time series')
    plot_parameters.add_argument('--log', 
                        action='store_true',
                        help='Enable logaritmic scale')
    plot_parameters.add_argument('--bins',
                        type=int,
                        metavar=('BINS'),
                        default=1,
                        help='Number of bins for the histogram (default: %(default)s)')
    plot_parameters.add_argument('--roll',
                        type=int,
                        metavar=('ROLL'),
                        default=90,
                        help='Rolling average (default: %(default)s)')
    plot_parameters.add_argument('--elnino',
                        action='store_true',
                        dest = 'elnino',
                        help='Plot Nino/Nina events')
    plot_parameters.add_argument('--no-show',
                        dest='show_flag',
                        action='store_false',
                        default=True,
                        help='Do not show the plot')

    return parser


def add_map_parameters_arguments(parser):
    """Argument parser for the map parameters."""
    map_parameters = parser.add_argument_group('Map parameters')
    map_parameters.add_argument('--vlim',
                        nargs=2,
                        metavar=('VMIN', 'VMAX'),
                        help='Velocity limit for the colorbar')
    map_parameters.add_argument('--interpolate',
                        metavar='GRANULARITY',
                        type=int,
                        help='Interpolate data')
    map_parameters.add_argument('--isolines',
                        nargs=1,
                        metavar='LEVELS',
                        help='Number of isolines to be plotted on the map')
    map_parameters.add_argument('--cumulate',
                        action='store_true',
                        help='Cumulate data')
    map_parameters.add_argument('--average',
                        choices={'D','W','M','Y', None},
                        nargs='?',
                        default=None,
                        const='D',
                        metavar='TIME_PERIOD',
                        help='Average data, default is daily')
    map_parameters.add_argument('--colorbar',
                        nargs=1,
                        default='viridis',
                        metavar='COLORBAR',
                        help='Colorbar, default is %(default)s')

    return parser


def add_save_arguments(parser):
    """Argument parser for the save options."""
    save = parser.add_argument_group('Save options')
    save.add_argument('--save',
                      choices={'volcano-name', 'volcano-id', None},
                      dest='save',
                      default=None,
                      const='volcano-name',
                      nargs='?',
                      help='Save the plot. If --save is provided without a value, default is %(const)s.')
    save.add_argument('--outdir',
                        type=str,
                        default=os.getcwd(),
                        metavar='PATH',
                        help='Folder to save the plot, default is %(default)s')

    return parser


def parse_polygon(polygon):
    """
    Parses a polygon string retreive from ASF vertex tool and extracts the latitude and longitude coordinates.

    Args:
        polygon (str): The polygon string in the format "POLYGON((lon1 lat1, lon2 lat2, ...))".

    Returns:
        tuple: A tuple containing the latitude and longitude coordinates as lists.
               The latitude list contains the minimum and maximum latitude values.
               The longitude list contains the minimum and maximum longitude values.
    """
    latitude = []
    longitude = []
    pol = polygon.replace("POLYGON((", "").replace("))", "")

    # Split the string into a list of coordinates
    for word in pol.split(','):
        if (float(word.split(' ')[1])) not in latitude:
            latitude.append(float(word.split(' ')[1]))
        if (float(word.split(' ')[0])) not in longitude:
            longitude.append(float(word.split(' ')[0]))

    longitude = [round(min(longitude),2), round(max(longitude),2)]
    latitude = [round(min(latitude),2), round(max(latitude),2)]

    return latitude, longitude


def parse_coordinates(coordinates):
    """
    Parse the given coordinates string and convert it into a list of floats.

    Args:
        coordinates (str): The coordinates string to be parsed.

    Returns:
        list: A list of floats representing the parsed coordinates.

    Raises:
        ValueError: If the coordinates string is invalid.

    """
    if isinstance(coordinates, str):
        coordinates = coordinates.replace("'", '').replace('"', '')

        try:
            if ',' in coordinates:
                coordinates = coordinates.split(',')

            elif ':' in coordinates:
                coordinates = coordinates.split(':')
                coordinates = [float(i) for i in coordinates]

            elif ' ' in coordinates:
                coordinates = coordinates.split(' ')
                coordinates = [float(i) for i in coordinates]

            else:
                coordinates = [float(coordinates), float(coordinates)]

        except ValueError:
            msg=f'Error: {coordinates} invalid coordinate/s'
            raise ValueError(msg)

        return coordinates

    else:
        coordinates = [coordinates, coordinates]

        return coordinates


###################### TEST AREA ##########################

# from precip.plotter_functions import *
# from precip.helper_functions import sql_extract_precipitation
# import os
# # from precip.plotter_functions import bar_plotter_2, plot_elninos
# # from matplotlib import pyplot as plt

# date_list = generate_date_list('20000601', '20010603')

# eruption_dates, lalo = extract_volcanoes_info(None, 'Merapi')
# latitude, longitude = adapt_coordinates(lalo[0], lalo[1])

# precipitation = sql_extract_precipitation(latitude, longitude, date_list, gpm_dir)

# precipitation = from_nested_to_float(precipitation)

# sys.exit(0)

#################### END TEST AREA ########################

def main(iargs=None, namespace=None):

    inps = create_parser(iargs, namespace)
    # FA: suggest function inps = configure_inps(inps)
    # FA: suggest function inps = configure_plot_settings(inps)

    inps.dir = PRECIP_DIR
    os.makedirs(PRECIP_DIR, exist_ok=True)


    # FA: The prompt_subplot function needs to be separated into functions for download, data preparation (write data into inps.outdir) and plotting.
    fig, axes = prompt_subplots(inps)

    return fig, axes

if __name__ == "__main__":
    main()
