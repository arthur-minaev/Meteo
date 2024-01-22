import os, ee, geemap
from datetime import date, timedelta
import geopandas as gpd
try:
    ee.Initialize()
except:
    ee.Authenticate()
from temp_files import StopFromStorage

shp = r"\\172.21.195.2\thematic\!projects\GPA2\SMI\Новосибирск\suzunsky.geojson"
out_dir = r"\\172.21.195.2\thematic\!projects\GPA2\SMI\Новосибирск\era5\era5_2022       "
start_date = date(2022, 5, 1)
end_date = date(2022, 10, 1)
indicators = ['temperature_2m', 'total_precipitation_sum']

def period(end_date, start_date):
    return (end_date - start_date).days

@StopFromStorage
def aoi(shp):
    drought = geemap.geojson_to_ee(shp)
    return drought.geometry()

def dates(start_date, end_date):
    return [[(start_date + timedelta(days=i)).isoformat(), (start_date + timedelta(days=i+1)).isoformat()]
            for i in range(0, period(end_date, start_date))]

def download(start_date, end_date, indicators, roi, out_dir, dataset="ECMWF/ERA5_LAND/DAILY_AGGR"):
    for date_list in dates(start_date, end_date):
        for indicator in indicators:
            data = ee.ImageCollection(dataset).select(indicator).filter(ee.Filter.date(date_list[0], date_list[1]))
            filename = os.path.join(out_dir, f"ERA5_{indicator}_{date_list[0].replace('-', '')}.tif")
            image = data.toBands().clip(roi).unmask()
            geemap.ee_export_image(image, filename=filename, region=roi, file_per_band=False)

roi = aoi(shp)
download(start_date, end_date, indicators, roi, out_dir)