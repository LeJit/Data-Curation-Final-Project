import marimo

__generated_with = "0.18.3"
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
    return (load_dotenv,)


@app.cell
def _():
    import json
    import polars as pl
    return json, pl


@app.cell
def _():
    import altair as alt
    return (alt,)


@app.cell
def _(load_dotenv):
    load_dotenv()
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Configuration
    """)
    return


@app.cell
def _():
    ## Demo Video showcasing authenticity
    ## Add small procedure for Professor to run the same project
    ## The Professor is the one reviewing the professor
    return


@app.cell
def _():
    # Configuration parameters
    CONFIG = {
        'project_id': 'coursera-bigquery-359202', # Include 
        'geojson_path': '../../data/colossus.json',
        'date_start': '2022-01-01',
        'date_end': '2023-01-01',
        'cloud_threshold': 5,
        'zoom_level': 14,
        'satellite': 'COPERNICUS/S2_SR_HARMONIZED',
        'scale': 10,  # meters per pixel for Sentinel-2
        'max_pixels': 1e8,  # Maximum pixels for export/computation
        'vis_params': {
            'min': 0,
            'max': 3000,
            'bands': ['B4', 'B3', 'B2']  # True color composite
        }
    }
    return (CONFIG,)


@app.cell
def _(CONFIG, ee):
    try:
        # Attempt to initialize GEE without authentication, 
        # which may work if you've done it recently or if running locally.
        ee.Initialize(project=CONFIG['project_id'])
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
    mo.md(r"""
    # Data Collection Parameters
    """)
    return


@app.cell
def _(CONFIG, json):
    with open(CONFIG['geojson_path']) as f:
        expanded_geojson_data = json.load(f)
    return (expanded_geojson_data,)


@app.cell
def _(ee, expanded_geojson_data):
    aoi_geometry_10ha = ee.FeatureCollection(expanded_geojson_data['features']).geometry()
    return (aoi_geometry_10ha,)


@app.cell
def _(CONFIG, aoi_geometry_10ha, ee):
    L8_collection = (ee.ImageCollection(CONFIG['satellite']) \
        .filterDate(CONFIG['date_start'], CONFIG['date_end']) \
        .filterBounds(aoi_geometry_10ha)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CONFIG['cloud_threshold'])))
    return (L8_collection,)


@app.cell
def _(CONFIG, aoi_geometry_10ha):
    # Use bounded operation to avoid memory issues with large geometries
    centroid_info = aoi_geometry_10ha.centroid(maxError=CONFIG['scale']).getInfo()
    print(f"Expanded AOI successfully loaded. Center: {centroid_info['coordinates']}")
    return


@app.cell
def _(L8_collection, aoi_geometry_10ha):
    median_composite = L8_collection.median().clip(aoi_geometry_10ha)
    return (median_composite,)


@app.cell
def _(median_composite):
    median_composite
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Display on Map
    """)
    return


@app.cell
def _(CONFIG):
    # Use visualization parameters from config
    vis_params_rgb = CONFIG['vis_params']
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
def _(CONFIG, Map, aoi_geometry_10ha):
    Map.centerObject(aoi_geometry_10ha, CONFIG['zoom_level'])
    return


@app.cell
def _(Map):
    map_html = Map.to_html()
    return (map_html,)


@app.cell
def _(map_html, mo):
    mo.Html(map_html)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 2024-2025 Development
    """)
    return


@app.cell
def _():
    return


@app.cell
def _(CONFIG, L8_collection, aoi_geometry_10ha, ee, mo):
    # Create the 2024-2025 collection
    L8_collection_2024 = (ee.ImageCollection(CONFIG['satellite'])
        .filterDate('2024-01-01', '2025-01-01')
        .filterBounds(aoi_geometry_10ha)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CONFIG['cloud_threshold'])))

    # Create median composite
    median_composite_2024 = L8_collection_2024.median().clip(aoi_geometry_10ha)

    # Check how many images were used
    image_count_2022 = L8_collection.size().getInfo()
    image_count_2024 = L8_collection_2024.size().getInfo()

    mo.md(f"""
    ### Image Collection Summary
    - **2022-2023**: {image_count_2022} images
    - **2024-2025**: {image_count_2024} images
    """)
    return (median_composite_2024,)


@app.cell
def _():
    return


@app.cell
def _(median_composite, median_composite_2024):
    # Calculate NDVI for 2022-2023 (using existing median_composite)
    ndvi_2022 = median_composite.normalizedDifference(['B8', 'B4']).rename('NDVI_2022')

    # Calculate NDVI for 2024-2025
    ndvi_2024 = median_composite_2024.normalizedDifference(['B8', 'B4']).rename('NDVI_2024')

    # Calculate the change (positive = vegetation increase, negative = decrease)
    ndvi_change = ndvi_2024.subtract(ndvi_2022).rename('NDVI_Change')

    # Create a mask for significant changes (|change| > 0.1)
    significant_change = ndvi_change.abs().gt(0.1)

    ndvi_change
    return ndvi_2022, ndvi_2024, ndvi_change, significant_change


@app.cell
def _(
    CONFIG,
    aoi_geometry_10ha,
    geemap,
    ndvi_2022,
    ndvi_2024,
    ndvi_change,
    significant_change,
):
    # Create map with both periods and changes
    change_map = geemap.Map()

    # 2022-2023 NDVI
    change_map.addLayer(
        ndvi_2022,
        {'min': -0.2, 'max': 0.8, 'palette': ['brown', 'yellow', 'lightgreen', 'darkgreen']},
        'NDVI 2022-2023'
    )

    # 2024-2025 NDVI
    change_map.addLayer(
        ndvi_2024,
        {'min': -0.2, 'max': 0.8, 'palette': ['brown', 'yellow', 'lightgreen', 'darkgreen']},
        'NDVI 2024-2025',
        shown=False
    )

    # NDVI Change (red = vegetation loss, green = vegetation gain)
    change_map.addLayer(
        ndvi_change,
        {'min': -0.5, 'max': 0.5, 'palette': ['red', 'white', 'green']},
        'NDVI Change'
    )

    # Highlight significant changes
    change_map.addLayer(
        ndvi_change.updateMask(significant_change),
        {'min': -0.5, 'max': 0.5, 'palette': ['darkred', 'white', 'darkgreen']},
        'Significant Changes (|Δ| > 0.1)'
    )

    # Add AOI boundary
    change_map.addLayer(
        aoi_geometry_10ha,
        {'color': 'FF0000', 'fillColor': '00000000'},
        'AOI Boundary'
    )

    change_map.centerObject(aoi_geometry_10ha, CONFIG['zoom_level'])
    return


@app.cell
def _():
    return


@app.cell
def _(CONFIG, aoi_geometry_10ha, ee, ndvi_2022, ndvi_2024, ndvi_change, pl):
    # Calculate statistics for both periods
    stats_2022 = ndvi_2022.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            ee.Reducer.stdDev(), '', True
        ).combine(
            ee.Reducer.minMax(), '', True
        ),
        geometry=aoi_geometry_10ha,
        scale=CONFIG['scale'],
        maxPixels=CONFIG['max_pixels']
    ).getInfo()

    stats_2024 = ndvi_2024.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            ee.Reducer.stdDev(), '', True
        ).combine(
            ee.Reducer.minMax(), '', True
        ),
        geometry=aoi_geometry_10ha,
        scale=CONFIG['scale'],
        maxPixels=CONFIG['max_pixels']
    ).getInfo()

    # Calculate change statistics
    change_stats = ndvi_change.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            ee.Reducer.stdDev(), '', True
        ).combine(
            ee.Reducer.minMax(), '', True
        ),
        geometry=aoi_geometry_10ha,
        scale=CONFIG['scale'],
        maxPixels=CONFIG['max_pixels']
    ).getInfo()

    # Create comparison dataframe
    comparison_df = pl.DataFrame({
        'Metric': ['Mean NDVI', 'Std Dev', 'Min NDVI', 'Max NDVI'],
        '2022-2023': [
            stats_2022['NDVI_2022_mean'],
            stats_2022['NDVI_2022_stdDev'],
            stats_2022['NDVI_2022_min'],
            stats_2022['NDVI_2022_max']
        ],
        '2024-2025': [
            stats_2024['NDVI_2024_mean'],
            stats_2024['NDVI_2024_stdDev'],
            stats_2024['NDVI_2024_min'],
            stats_2024['NDVI_2024_max']
        ]
    }).with_columns([
        (pl.col('2024-2025') - pl.col('2022-2023')).alias('Change')
    ])

    comparison_df
    return (change_stats,)


@app.cell
def _(CONFIG, alt, aoi_geometry_10ha, ee, ndvi_change, pl):
    # Calculate histogram of changes
    change_histogram = ndvi_change.reduceRegion(
        reducer=ee.Reducer.histogram(maxBuckets=100),
        geometry=aoi_geometry_10ha,
        scale=CONFIG['scale'],
        maxPixels=CONFIG['max_pixels']
    ).getInfo()

    # Extract histogram data
    hist_data = change_histogram['NDVI_Change']
    bins = hist_data['bucketMeans']
    counts = hist_data['histogram']

    change_hist_df = pl.DataFrame({
        'NDVI_Change': bins,
        'Pixel_Count': counts
    }, strict=False)

    # Create histogram
    change_hist_chart = alt.Chart(change_hist_df).mark_bar().encode(
        x=alt.X('NDVI_Change:Q', title='NDVI Change', bin=alt.Bin(maxbins=50)),
        y=alt.Y('Pixel_Count:Q', title='Number of Pixels'),
        color=alt.condition(
            alt.datum.NDVI_Change > 0,
            alt.value('green'),
            alt.value('red')
        )
    ).properties(
        title='Distribution of NDVI Changes (2022-2023 to 2024-2025)',
        width=700,
        height=400
    )

    change_hist_chart
    return


@app.cell
def _(CONFIG, alt, aoi_geometry_10ha, ee, mo, ndvi_change, pl):

    # Define change categories
    vegetation_loss_strong = ndvi_change.lt(-0.2)
    vegetation_loss_moderate = ndvi_change.gte(-0.2).And(ndvi_change.lt(-0.1))
    no_change = ndvi_change.gte(-0.1).And(ndvi_change.lte(0.1))
    vegetation_gain_moderate = ndvi_change.gt(0.1).And(ndvi_change.lte(0.2))
    vegetation_gain_strong = ndvi_change.gt(0.2)

    # Calculate area for each category (in square meters)
    pixel_area = ee.Image.pixelArea()

    area_loss_strong = vegetation_loss_strong.multiply(pixel_area).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=aoi_geometry_10ha,
        scale=CONFIG['scale'],
        maxPixels=CONFIG['max_pixels']
    ).getInfo()

    area_loss_moderate = vegetation_loss_moderate.multiply(pixel_area).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=aoi_geometry_10ha,
        scale=CONFIG['scale'],
        maxPixels=CONFIG['max_pixels']
    ).getInfo()

    area_no_change = no_change.multiply(pixel_area).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=aoi_geometry_10ha,
        scale=CONFIG['scale'],
        maxPixels=CONFIG['max_pixels']
    ).getInfo()

    area_gain_moderate = vegetation_gain_moderate.multiply(pixel_area).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=aoi_geometry_10ha,
        scale=CONFIG['scale'],
        maxPixels=CONFIG['max_pixels']
    ).getInfo()

    area_gain_strong = vegetation_gain_strong.multiply(pixel_area).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=aoi_geometry_10ha,
        scale=CONFIG['scale'],
        maxPixels=CONFIG['max_pixels']
    ).getInfo()

    # Create summary dataframe (convert to hectares)
    category_df = pl.DataFrame({
        'Category': [
            'Strong Loss (Δ < -0.2)',
            'Moderate Loss (-0.2 ≤ Δ < -0.1)',
            'No Change (-0.1 ≤ Δ ≤ 0.1)',
            'Moderate Gain (0.1 < Δ ≤ 0.2)',
            'Strong Gain (Δ > 0.2)'
        ],
        'Area_ha': [
            area_loss_strong.get('NDVI_Change', 0) / 10000,
            area_loss_moderate.get('NDVI_Change', 0) / 10000,
            area_no_change.get('NDVI_Change', 0) / 10000,
            area_gain_moderate.get('NDVI_Change', 0) / 10000,
            area_gain_strong.get('NDVI_Change', 0) / 10000
        ]
    })

    # Create pie chart
    pie_chart = alt.Chart(category_df).mark_arc().encode(
        theta=alt.Theta('Area_ha:Q', title='Area (hectares)'),
        color=alt.Color('Category:N', 
            scale=alt.Scale(
                domain=['Strong Loss (Δ < -0.2)', 'Moderate Loss (-0.2 ≤ Δ < -0.1)', 
                       'No Change (-0.1 ≤ Δ ≤ 0.1)', 'Moderate Gain (0.1 < Δ ≤ 0.2)', 
                       'Strong Gain (Δ > 0.2)'],
                range=['darkred', 'red', 'gray', 'lightgreen', 'darkgreen']
            )
        ),
        tooltip=['Category:N', alt.Tooltip('Area_ha:Q', format='.2f', title='Area (ha)')]
    ).properties(
        title='Vegetation Change Categories by Area',
        width=400,
        height=400
    )

    mo.vstack([category_df, pie_chart])
    return (
        area_gain_moderate,
        area_gain_strong,
        area_loss_moderate,
        area_loss_strong,
        area_no_change,
    )


@app.cell
def _():
    return


@app.cell
def _(
    CONFIG,
    aoi_geometry_10ha,
    geemap,
    median_composite,
    median_composite_2024,
    mo,
):


    # Create side-by-side comparison map
    comparison_map = geemap.Map()

    # 2022-2023 True Color
    comparison_map.addLayer(
        median_composite,
        CONFIG['vis_params'],
        '2022-2023 True Color'
    )

    # 2024-2025 True Color
    comparison_map.addLayer(
        median_composite_2024,
        CONFIG['vis_params'],
        '2024-2025 True Color',
        shown=False
    )

    comparison_map.addLayer(aoi_geometry_10ha, {'color': 'FF0000'}, 'AOI')
    comparison_map.centerObject(aoi_geometry_10ha, CONFIG['zoom_level'])

    mo.Html(comparison_map.to_html())
    return


@app.cell
def _(
    aoi_geometry_10ha,
    area_gain_moderate,
    area_gain_strong,
    area_loss_moderate,
    area_loss_strong,
    area_no_change,
    change_stats,
    mo,
):


    total_area = aoi_geometry_10ha.area().divide(10000).getInfo()  # in hectares

    vegetation_loss_area = (area_loss_strong.get('NDVI_Change', 0) + 
                           area_loss_moderate.get('NDVI_Change', 0)) / 10000
    vegetation_gain_area = (area_gain_strong.get('NDVI_Change', 0) + 
                           area_gain_moderate.get('NDVI_Change', 0)) / 10000

    net_change_pct = ((vegetation_gain_area - vegetation_loss_area) / total_area) * 100

    mo.md(f"""
    ## Vegetation Change Summary (2022-2023 → 2024-2025)

    ### Overall Statistics
    - **Total AOI Area**: {total_area:.2f} hectares
    - **Mean NDVI Change**: {change_stats['NDVI_Change_mean']:.3f}
    - **Net Vegetation Change**: {net_change_pct:+.2f}%

    ### Area Changes
    - **Vegetation Loss**: {vegetation_loss_area:.2f} ha ({(vegetation_loss_area/total_area*100):.1f}%)
    - **Vegetation Gain**: {vegetation_gain_area:.2f} ha ({(vegetation_gain_area/total_area*100):.1f}%)
    - **No Significant Change**: {area_no_change.get('NDVI_Change', 0)/10000:.2f} ha

    ### Interpretation
    - **Positive change** indicates vegetation increase (greening)
    - **Negative change** indicates vegetation decrease (browning/clearing)
    - **NDVI range**: -1 to +1 (higher = more vegetation)

    ### Key Findings
    {'📈 Net vegetation **increase** detected' if net_change_pct > 0 else '📉 Net vegetation **decrease** detected'}
    """)
    return


if __name__ == "__main__":
    app.run()
