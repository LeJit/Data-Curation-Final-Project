import marimo

__generated_with = "0.16.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    import ee
    import geemap
    import felt_python
    return ee, geemap


@app.cell
def _():
    import os
    from dotenv import load_dotenv
    return load_dotenv, os


@app.cell
def _():
    import json
    return (json,)


@app.cell
def _(load_dotenv):
    load_dotenv()
    return


@app.cell
def _(ee):
    try:
        # Attempt to initialize GEE without authentication, 
        # which may work if you've done it recently or if running locally.
        ee.Initialize(project="coursera-bigquery-359202")
        print("Google Earth Engine initialized successfully.")

    except Exception as e:
        # If initialization fails, run the interactive authentication flow.
        print("Initialization failed. Starting interactive authentication...")

        # 1. Authenticate using the Colab/Jupyter pattern
        # This generates a URL you must click.
        ee.Authenticate() 

        # 2. Re-initialize after authentication
        print("Authentication successful. Earth Engine initialized.")
    return


@app.cell
def _(mo):
    mo.md(r"""# Data Collection Parameters""")
    return


@app.cell
def _(json):
    with open("data/colossus.json") as f:
        expanded_geojson_data = json.load(f)
    return (expanded_geojson_data,)


@app.cell
def _(ee, expanded_geojson_data):
    aoi_geometry_10ha = ee.FeatureCollection(expanded_geojson_data['features']).geometry()
    return (aoi_geometry_10ha,)


@app.cell
def _(aoi_geometry_10ha, ee):
    L8_collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterDate('2022-01-01', '2023-01-01') \
        .filterBounds(aoi_geometry_10ha)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5)))
    return (L8_collection,)


@app.cell
def _(aoi_geometry_10ha):
    print(f"Expanded AOI successfully loaded. Center: {aoi_geometry_10ha.centroid().getInfo()['coordinates']}")
    return


@app.cell
def _(L8_collection, aoi_geometry_10ha):
    median_composite = L8_collection.median().clip(aoi_geometry_10ha)
    return (median_composite,)


@app.cell
def _(mo):
    mo.md(r"""### Display on Map""")
    return


@app.cell
def _():
    vis_params_rgb = {
        'min': 0,
        'max': 3000,
        'bands': ['B4', 'B3', 'B2'] 
    }
    return (vis_params_rgb,)


@app.cell
def _(geemap):
    Map = geemap.Map()
    return (Map,)


@app.cell
def _(Map, median_composite, vis_params_rgb):
    Map.addLayer(
        median_composite, 
        vis_params_rgb, 
        'Colossus Data Center (True Color Composite)'
    )
    return


@app.cell
def _(Map, aoi_geometry_10ha):
    Map.addLayer(
        aoi_geometry_10ha, 
        {'color': 'FF0000', 'fillColor': '00000000'}, # Red outline, transparent fill
        'AOI Boundary'
    )
    return


@app.cell
def _(Map, aoi_geometry_10ha):
    Map.centerObject(aoi_geometry_10ha, 14)
    return


@app.cell
def _(Map):
    Map
    return


@app.cell
def _(mo):
    mo.md(r"""# Felt Map Generation""")
    return


@app.cell
def _(os):
    FELT_API_KEY = os.environ.get("FELT_ACCESS_TOKEN")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
