import marimo

__generated_with = "0.18.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import ee
    import geemap
    import cecil
    import xarray as xr
    import polars as pl
    import altair as alt
    import numpy as np
    import pystac
    import json
    import os
    from datetime import datetime
    from pathlib import Path
    from dotenv import load_dotenv

    load_dotenv()
    return Path, alt, cecil, datetime, ee, json, mo, np, os, pl, pystac, xr


@app.cell
def _(mo):
    mo.md(r"""
    # Combined Geospatial Analysis: Earth Engine & Cecil

    This notebook combines data from:
    1.  **Google Earth Engine**: Sentinel-2 NDVI (Vegetation Index)
    2.  **Cecil**: "Land Cover 9-Class" dataset

    **Temporal Analysis**:
    - Period 1: **2022-2023**
    - Period 2: **2024-2025**
    """)
    return


@app.cell
def _(ee, json, os):
    # Configuration
    CONFIG = {
        'project_id': os.getenv('GEE_PROJECT_ID'), 
        'geojson_path': 'data/colossus.json',
        'cecil_dataset_id': '89d81a76-3c42-4365-92c2-c1b8a00aacd5',
        'date_start_1': '2022-01-01',
        'date_end_1': '2023-01-01',
        'date_start_2': '2024-01-01',
        'date_end_2': '2025-01-01',
        'cloud_threshold': 5,
        'zoom_level': 14,
        'satellite': 'COPERNICUS/S2_SR_HARMONIZED',
        'scale': 10,
        'vis_params': {
            'min': 0,
            'max': 3000,
            'bands': ['B4', 'B3', 'B2']
        }
    }

    # Initialize Earth Engine
    try:
        ee.Initialize(project=CONFIG['project_id'])
        print("Google Earth Engine initialized successfully.")
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=CONFIG['project_id'])

    # Load AOI
    with open(CONFIG['geojson_path']) as f_aoi:
        expanded_geojson_data = json.load(f_aoi)

    aoi_geometry = ee.FeatureCollection(expanded_geojson_data['features']).geometry()
    return CONFIG, aoi_geometry


@app.cell
def _(CONFIG, cecil, mo):
    # Load Cecil Data
    client = cecil.Client()
    print(f"Loading Cecil Dataset ID: {CONFIG['cecil_dataset_id']}...")
    try:
        cecil_ds = client.load_xarray(subscription_id=CONFIG['cecil_dataset_id'])
        print("Cecil Dataset loaded successfully.")

        # Filter for the two time windows
        # Assuming Cecil dataset has a 'time' coordinate
        cecil_22 = cecil_ds.sel(time=slice(CONFIG['date_start_1'], CONFIG['date_end_1']))
        cecil_24 = cecil_ds.sel(time=slice(CONFIG['date_start_2'], CONFIG['date_end_2']))

        mo.md(f"""
        ### Cecil Data Loaded
        - **2022-2023 Slices**: {cecil_22.time.size}
        - **2024-2025 Slices**: {cecil_24.time.size}
        """)

    except Exception as e:
        print(f"Error loading Cecil dataset: {e}")
        cecil_ds = None
        cecil_22 = None
        cecil_24 = None
    return cecil_22, cecil_24


@app.cell
def _(CONFIG, aoi_geometry, ee):
    def get_ee_xarray(start_date, end_date):
        """Get EE data using EE's native download URL"""
        collection = (ee.ImageCollection(CONFIG['satellite'])
            .filterDate(start_date, end_date)
            .filterBounds(aoi_geometry)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CONFIG['cloud_threshold'])))

        composite = collection.median().clip(aoi_geometry)
        ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI')

        import tempfile
        import rioxarray
        import requests

        # Get download URL directly from EE (uses your authenticated project)
        url = ndvi.getDownloadURL({
            'scale': CONFIG['scale'],
            'region': aoi_geometry,
            'crs': 'EPSG:4326',
            'format': 'GEO_TIFF'
        })

        # Download the file
        tmp_file = tempfile.mktemp(suffix='.tif')
        response = requests.get(url)

        with open(tmp_file, 'wb') as f:
            f.write(response.content)

        # Load the file
        ds = rioxarray.open_rasterio(tmp_file).to_dataset(name='NDVI')

        # Clean up
        import os
        os.remove(tmp_file)

        return ds

    ee_ds_22 = get_ee_xarray(CONFIG['date_start_1'], CONFIG['date_end_1'])
    ee_ds_24 = get_ee_xarray(CONFIG['date_start_2'], CONFIG['date_end_2'])

    print(f"EE 2022 shape: {ee_ds_22['NDVI'].shape}")
    print(f"EE 2024 shape: {ee_ds_24['NDVI'].shape}")
    return ee_ds_22, ee_ds_24


@app.cell
def _(np, xr):
    def join_datasets(ee_data, cecil_data, time_method='first'):
        """
        Join Earth Engine and Cecil datasets with proper CRS handling.
        """
        if cecil_data is None or ee_data is None:
            raise ValueError("Both datasets must be provided")

        # Get Cecil variable
        var_name = list(cecil_data.data_vars)[0]

        # Handle time dimension in Cecil data
        if 'time' in cecil_data.dims and cecil_data.time.size > 1:
            if time_method == 'first':
                cecil_static = cecil_data.isel(time=0)
            elif time_method == 'mean':
                cecil_static = cecil_data.mean(dim='time')
            elif time_method == 'median':
                cecil_static = cecil_data.median(dim='time')
        else:
            cecil_static = cecil_data.isel(time=0) if 'time' in cecil_data.dims else cecil_data

        # Get EE data (remove band dimension)
        if 'band' in ee_data.dims:
            ee_spatial = ee_data['NDVI'].isel(band=0)
        else:
            ee_spatial = ee_data['NDVI']

        # Set up CRS for both datasets
        import rioxarray

        # Cecil is in Web Mercator (EPSG:3857) based on coordinate values
        cecil_with_crs = cecil_static[var_name].rio.write_crs("EPSG:3857", inplace=True)

        # EE is in geographic coordinates (EPSG:4326)
        ee_with_crs = ee_spatial.rio.write_crs("EPSG:4326", inplace=True)

        # Reproject Cecil from Web Mercator to Geographic to match EE
        cecil_reprojected = cecil_static[var_name].rio.reproject_match(ee_spatial)

        # Create combined dataset
        combined = xr.Dataset({
            'NDVI': ee_spatial,
            'land_cover': cecil_reprojected
        })

        print(f"Combined NDVI shape: {combined['NDVI'].shape}")
        print(f"Combined land_cover shape: {combined['land_cover'].shape}")
        print(f"land_cover has data: {not np.isnan(combined['land_cover'].values).all()}")
        print(f"land_cover unique values: {np.unique(combined['land_cover'].values[~np.isnan(combined['land_cover'].values)])}")

        return combined
    return (join_datasets,)


@app.cell
def _(cecil_22, cecil_24, ee_ds_22, ee_ds_24, join_datasets, mo):
    # Use the updated function
    combined_22 = join_datasets(ee_ds_22, cecil_22, time_method='first')
    combined_24 = join_datasets(ee_ds_24, cecil_24, time_method='first')

    mo.vstack([
        mo.md("### Combined Dataset 2022-2023"),
        combined_22,
        mo.md("### Combined Dataset 2024-2025"),
        combined_24
    ])
    return combined_22, combined_24


@app.cell
def _(np, pl):
    def calculate_stats(combined_ds, period_label):
        """Calculate statistics from combined dataset"""
        # Remove time dimension from NDVI if it exists
        if 'time' in combined_ds['NDVI'].dims:
            ndvi_data = combined_ds['NDVI'].isel(time=0).squeeze()
        else:
            ndvi_data = combined_ds['NDVI'].squeeze()

        # Also squeeze land_cover in case it has singleton dimensions
        lc_data = combined_ds['land_cover'].squeeze()

        # Flatten arrays
        ndvi_flat = ndvi_data.values.flatten()
        lc_flat = lc_data.values.flatten()

        # Ensure both arrays have the same length
        if len(ndvi_flat) != len(lc_flat):
            raise ValueError(f"Array length mismatch: NDVI={len(ndvi_flat)}, land_cover={len(lc_flat)}")

        # Remove NaN values
        mask = ~np.isnan(ndvi_flat) & ~np.isnan(lc_flat)

        df = pl.DataFrame({
            'ndvi': ndvi_flat[mask],
            'land_cover': lc_flat[mask].astype(int),
            'period': period_label
        })

        return df.group_by('land_cover').agg([
            pl.col('ndvi').mean().alias('mean_ndvi'),
            pl.col('ndvi').std().alias('std_ndvi'),
            pl.len().alias('pixel_count')
        ]).sort('land_cover')
    return (calculate_stats,)


@app.cell
def _(calculate_stats, combined_22, combined_24):
    stats_22 = calculate_stats(combined_22, '2022-2023')
    stats_24 = calculate_stats(combined_24, '2024-2025')
    return stats_22, stats_24


@app.cell
def _(pl):
    # Define Land Cover class names from Cecil documentation
    # https://docs.cecil.earth/Land-Cover-9-Class-111ef16bbbe481c0bb41e6e79ec441c8
    LAND_COVER_CLASSES = {
        1: 'Water',
        2: 'Trees',
        3: 'Grass',
        4: 'Flooded Vegetation',
        5: 'Crops',
        6: 'Scrub/Shrub',
        7: 'Built Area',
        8: 'Bare Ground',
        9: 'Snow/Ice',
        11: 'Clouds'
    }

    def map_land_cover_names(df):
        """Map land cover indices to class names using when-then chain"""
        # Build the mapping expression
        mapping_expr = pl.when(pl.col('land_cover') == 1).then(pl.lit('Water'))
        for code, name in list(LAND_COVER_CLASSES.items())[1:]:
            mapping_expr = mapping_expr.when(pl.col('land_cover') == code).then(pl.lit(name))
        mapping_expr = mapping_expr.otherwise(pl.lit('Unknown'))

        return df.with_columns(
            mapping_expr.alias('land_cover_name')
        ).select([
            'land_cover',
            'land_cover_name',
            'mean_ndvi',
            'std_ndvi',
            'pixel_count'
        ])
    return (map_land_cover_names,)


@app.cell
def _(map_land_cover_names, mo, stats_22, stats_24):
    # Apply mapping to stats
    stats_22_labeled = map_land_cover_names(stats_22)
    stats_24_labeled = map_land_cover_names(stats_24)

    mo.vstack([
        mo.md("### Statistics 2022-2023 (with labels)"),
        stats_22_labeled,
        mo.md("### Statistics 2024-2025 (with labels)"),
        stats_24_labeled
    ])
    return stats_22_labeled, stats_24_labeled


@app.cell
def _(alt, pl, stats_22_labeled, stats_24_labeled):
    # Update visualization with class names
    viz_df = pl.concat([
        stats_22_labeled.with_columns(pl.lit("2022-2023").alias("Period")),
        stats_24_labeled.with_columns(pl.lit("2024-2025").alias("Period"))
    ])

    chart_comparison = alt.Chart(viz_df).mark_bar().encode(
        x=alt.X('Period:N', title='Time Period'),
        y=alt.Y('mean_ndvi:Q', title='Mean NDVI', scale=alt.Scale(domain=[0, 1])),
        color=alt.Color('Period:N', scale=alt.Scale(scheme='category10')),
        column=alt.Column(
            'land_cover_name:N', 
            title='Land Cover Class',
            header=alt.Header(titleOrient="bottom", labelOrient="bottom", labelAngle=0)
        ),
        tooltip=[
            alt.Tooltip('land_cover_name:N', title='Land Cover'),
            alt.Tooltip('Period:N', title='Period'),
            alt.Tooltip('mean_ndvi:Q', title='Mean NDVI', format='.4f'),
            alt.Tooltip('pixel_count:Q', title='Pixel Count')
        ]
    ).properties(
        title='Mean NDVI by Land Cover Class: 2022-2023 vs 2024-2025',
        width=120,
        height=200
    )

    chart_comparison
    return (chart_comparison,)


@app.cell
def _(map_land_cover_names, mo, pl, stats_22, stats_24):
    # Calculate changes with labels
    def calculate_changes_labeled(stats_22, stats_24):
        """Calculate changes between two periods with labels"""
        # Add labels to both dataframes
        stats_22_labeled = map_land_cover_names(stats_22)
        stats_24_labeled = map_land_cover_names(stats_24)

        # Join the two dataframes on land_cover
        changes = stats_22_labeled.join(
            stats_24_labeled.select(['land_cover', 'mean_ndvi', 'pixel_count']),
            on='land_cover',
            how='inner',
            suffix='_24'
        ).with_columns([
            # Calculate absolute and relative changes
            (pl.col('mean_ndvi_24') - pl.col('mean_ndvi')).alias('ndvi_change'),
            ((pl.col('mean_ndvi_24') - pl.col('mean_ndvi')) / pl.col('mean_ndvi') * 100).alias('ndvi_pct_change'),
            (pl.col('pixel_count_24') - pl.col('pixel_count')).alias('area_change'),
            ((pl.col('pixel_count_24') - pl.col('pixel_count')) / pl.col('pixel_count') * 100).alias('area_pct_change')
        ]).select([
            'land_cover',
            'land_cover_name',
            'mean_ndvi',
            'mean_ndvi_24',
            'ndvi_change',
            'ndvi_pct_change',
            'pixel_count',
            'pixel_count_24',
            'area_change',
            'area_pct_change'
        ])

        return changes

    changes_df = calculate_changes_labeled(stats_22, stats_24)

    mo.vstack([
        mo.md("### Change Analysis (2022-2023 → 2024-2025)"),
        changes_df
    ])
    return (changes_df,)


@app.cell
def _(
    CONFIG,
    Path,
    changes_df,
    chart_comparison,
    combined_22,
    combined_24,
    datetime,
    json,
    pystac,
    stats_22,
    stats_24,
):
    # Output Generation

    output_dir = Path("outputs")
    reports_dir = output_dir / "reports"
    figures_dir = output_dir / "figures"

    reports_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Save Figure
    chart_path = figures_dir / f"ndvi_comparison_{timestamp}.png"
    try:
        chart_comparison.save(str(chart_path))
    except Exception as e:
        print(f"Could not save chart: {e}")

    # 2. Report
    report_content = f"""# Temporal Geospatial Analysis Report

    **Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    **AOI:** {CONFIG['geojson_path']}

    ## Executive Summary
    Comprehensive analysis of vegetation health (NDVI) across land cover classes between **2022-2023** and **2024-2025** for the Colossus supercomputer site. Analysis combines Sentinel-2 multispectral imagery with Cecil's 9-class land cover dataset.

    ## Study Area
    **Location**: Colossus Supercomputer Site
    **Total Pixels**: {stats_22['pixel_count'].sum():,} (Period 1), {stats_24['pixel_count'].sum():,} (Period 2)
    **Coverage Area**: ~{(stats_22['pixel_count'].sum() * (CONFIG['scale']/1000)**2):.2f} km²


    ## Methodology

    ### Data Sources
    - **Vegetation Index**: Sentinel-2 Surface Reflectance (COPERNICUS/S2_SR_HARMONIZED)
      - NDVI calculated from B8 (NIR) and B4 (Red) bands
      - Cloud threshold: <5%
      - Spatial resolution: 10m
  
    - **Land Cover Classification**: Cecil Land Cover 9-Class
      - Dataset ID: {CONFIG['cecil_dataset_id']}
      - Classes: Water, Trees, Grass, Flooded Vegetation, Crops, Scrub/Shrub, Built Area, Bare Ground, Snow/Ice
      - [Documentation](https://docs.cecil.earth/Land-Cover-9-Class-111ef16bbbe481c0bb41e6e79ec441c8)

    ### Processing Steps
    1. Temporal compositing using median values to reduce cloud interference
    2. NDVI calculation: (NIR - Red) / (NIR + Red)
    3. CRS reprojection from EPSG:3857 (Cecil) to EPSG:4326 (Earth Engine)
    4. Statistical aggregation by land cover class

    ## Results

    ### 2022-2023
    {stats_22.to_pandas().to_markdown(index=False) if stats_22 is not None else "No Data"}

    ### 2024-2025
    {stats_24.to_pandas().to_markdown(index=False) if stats_24 is not None else "No Data"}

    ### Change Analysis
    {changes_df.to_pandas().to_markdown(index=False) if changes_df is not None else "No Data"}

    ![NDVI Comparison Chart](../figures/{chart_path.name})
    """
    report_path = reports_dir / f"final_report_{timestamp}.md"
    report_path.write_text(report_content)
    print(f"Report saved to: {report_path}")

    # 3. Create PyStac Items
    def save_stac(combined_ds, period_label, stats_df):
        if combined_ds is None: return

        # Define metadata directory
        metadata_dir = Path("data/metadata")
        metadata_dir.mkdir(parents=True, exist_ok=True)

        item_id = f"combined-analysis-{period_label}-{timestamp}"
        stac_item = pystac.Item(
            id=item_id,
            geometry=None, 
            bbox=None,
            datetime=datetime.now(),
            properties={
                "period": period_label,
                "platform": "Sentinel-2",
                "cecil:subscription_id": CONFIG['cecil_dataset_id'],
                "cecil:documentation": "https://docs.cecil.earth/Land-Cover-9-Class-111ef16bbbe481c0bb41e6e79ec441c8",
                "colossus:wikipedia": "https://en.wikipedia.org/wiki/Colossus_(supercomputer)"
            }
        )
        stac_item.add_asset(
            key="report",
            asset=pystac.Asset(href=str(report_path), media_type="text/markdown", title="Analysis Report")
        )
        stac_path = metadata_dir / f"combined_analysis_{period_label}.json"

        with open(stac_path, 'w') as f_stac:
            json.dump(stac_item.to_dict(), f_stac, indent=2, default=str)
        print(f"STAC saved: {stac_path}")

    save_stac(combined_22, "2022_2023", stats_22)
    save_stac(combined_24, "2024_2025", stats_24)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
