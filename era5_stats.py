import os
from osgeo import gdal, gdal_array, gdalconst, ogr, osr
import geopandas as gpd
import pandas as pd
import pyproj
from datetime import date, timedelta
import openpyxl

from check_raster_files import *
from paths import *
from vector_geometry import *

grid = "D:\era5\era5_grid.geojson"
era5_2020 = "D:\era5\era5_2020"
era5_2021 = "D:\era5\era5_2021"
era5_2022 = "D:\era5\era5_2022"
era5_2023 = "D:\era5\era5_2023"
start_date = date(2020, 5, 1)
end_date = date(2020, 10, 1)


def ConvertDigits(digit):
    if digit < 10:
        return f'0{digit}'
    else:
        return f'{digit}'

def period(end_date, start_date):
    return (end_date - start_date).days

def dates(start_date, end_date):
    return [f'{ConvertDigits((start_date + timedelta(days=i)).month)}.' \
            f'{ConvertDigits((start_date + timedelta(days=i)).day)}'
            for i in range(0, period(end_date, start_date))]

def GetCellGeometry(grid, idx):
    gdf = gpd.read_file(grid)
    gdf_sel = gdf.query(f"id=={idx}")
    gdf_sel_wgs = gdf_sel.to_crs('EPSG:4326')
    vector = TempName(idx, 'shp')
    gdf_sel_wgs.to_file(vector)
    return vector

def GetValue(raster_in, raster_out, vector, rnd):
    params = {'__vector_clipper': VectorClipper(vector, 'YES'), '__force_warp': True}
    SetRaster(rpath=raster_in, tpath= raster_out, miss=None, **params)
    ds = gdal.Open(raster_out)
    arr = ds.ReadAsArray()
    ds = None
    return round(arr[0][0], rnd)

gdf = gpd.read_file(grid)
for i in range(1, len(gdf) + 1):
    print(f'id: {i}')
    # extract data
    vector = GetCellGeometry(grid, i)
    temps_list = []
    prec_list = []
    folders = [era5_2020, era5_2021, era5_2022, era5_2023]
    for folder in folders:
        temps = []
        prec = []
        for file in sorted(Files(folder)):
            name = SplitPath(file)[1]
            raster_out = TempName(name, 'tif')
            if re.search('temperature', file):
                value = GetValue(file, raster_out, vector, 2) - 273.15
                temps.append(value)
            else:
                value = GetValue(file, raster_out, vector, 3) * 1000
                prec.append(value)
        temps_list.append(temps)
        prec_list.append(prec)

    # edit data for 2023
    temp_2023 = [None] * len(temps_list[0])
    for j in range(len(temps_list[3])):
        temp_2023[j] = temps_list[3][j]
    prec_2023 = [None] * len(prec_list[0])
    for k in range(len(prec_list[3])):
        prec_2023[k] = prec_list[3][k]

    # export data
    data = {'dates': dates(start_date, end_date),
            '2020_temp': temps_list[0], '2021_temp': temps_list[1], '2022_temp': temps_list[2], '2023_temp': temp_2023,
            '2020_prec': prec_list[0], '2021_prec': prec_list[1], '2022_prec': prec_list[2], '2023_prec': prec_2023}
    df = pd.DataFrame(data)
    print(f'id: {i}')
    with pd.ExcelWriter(f'tab{i}.xlsx') as writer:
        df.to_excel(writer, sheet_name=f"{i}")
