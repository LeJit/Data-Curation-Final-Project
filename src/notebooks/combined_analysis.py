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
    return (
        Path,
        alt,
        cecil,
        datetime,
        ee,
        geemap,
        json,
        load_dotenv,
        mo,
        np,
        os,
        pl,
        pystac,
        xr,
    )


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
def _(ee, json):
    # Configuration
    CONFIG = {
        'project_id': 'coursera-bigquery-359202', 
        'geojson_path': '../../data/colossus.json',
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
    
    return CONFIG, aoi_geometry, expanded_geojson_data


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
        
    return cecil_22, cecil_24, cecil_ds, client


@app.cell
def _(CONFIG, aoi_geometry, ee, xr):
    # Earth Engine Data Retrieval & Conversion
    
    roi = aoi_geometry.bounds()

    def get_ee_xarray(start_date, end_date):
        collection = (ee.ImageCollection(CONFIG['satellite'])
            .filterDate(start_date, end_date)
            .filterBounds(aoi_geometry)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CONFIG['cloud_threshold'])))
        
        # Median Composite -> NDVI
        composite = collection.median().clip(aoi_geometry)
        ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI')
        
        # Open as Xarray
        ds = xr.open_dataset(
            ndvi,
            engine='ee',
            geometry=roi,
            scale=CONFIG['scale'],
            crs='EPSG:4326'
        )
        return ds

    # 1. 2022-2023
    ee_ds_22 = get_ee_xarray(CONFIG['date_start_1'], CONFIG['date_end_1'])
    
    # 2. 2024-2025
    ee_ds_24 = get_ee_xarray(CONFIG['date_start_2'], CONFIG['date_end_2'])
    
    return ee_ds_22, ee_ds_24, get_ee_xarray, roi


@app.cell
def _(cecil_22, cecil_24, ee_ds_22, ee_ds_24, mo, pl):
    # Geospatial Join and Analysis
    
    results = {}
    
    def process_period(cecil_data, ee_data, period_name):
        if cecil_data is None or ee_data is None:
            return None, None
        
        try:
            # 1. Align Cecil to EE (Resample/Regrid)
            # Assuming 'class_label' is the variable
            var_name = list(cecil_data.data_vars)[0]
            
            # Take median/mode of Cecil time series if multiple steps exist, or just first
            if 'time' in cecil_data.dims:
                cecil_static = cecil_data.isel(time=0) # Simplified for now
            else:
                cecil_static = cecil_data
                
            cecil_interp = cecil_static[var_name].interp_like(ee_data, method='nearest')
            
            # 2. Merge
            combined = ee_data.merge(cecil_interp.rename('land_cover'))
            
            # 3. Stats
            df_pd = combined.to_dataframe().reset_index().dropna()
            df_pl = pl.from_pandas(df_pd)
            
            stats = df_pl.group_by('land_cover').agg([
                pl.col('NDVI').mean().alias('mean_ndvi'),
                pl.col('NDVI').count().alias('pixel_count')
            ]).sort('mean_ndvi', descending=True)
            
            return combined, stats
            
        except Exception as e:
            print(f"Error processing {period_name}: {e}")
            return None, None

    # Process both periods
    combined_22, stats_22 = process_period(cecil_22, ee_ds_22, "2022-2023")
    combined_24, stats_24 = process_period(cecil_24, ee_ds_24, "2024-2025")
    
    mo.md("### Joining Complete")
    return combined_22, combined_24, process_period, results, stats_22, stats_24


@app.cell
def _(alt, mo, pl, stats_22, stats_24):
    # Visualization: Compare 2022 vs 2024
    
    if stats_22 is None or stats_24 is None:
        chart = mo.md("Insufficient data for visualization.")
    else:
        # Prepare combined DF for plotting
        s22 = stats_22.with_columns(pl.lit("2022-2023").alias("Period"))
        s24 = stats_24.with_columns(pl.lit("2024-2025").alias("Period"))
        
        viz_df = pl.concat([s22, s24])
        
        chart = alt.Chart(viz_df).mark_bar().encode(
            x=alt.X('Period:N', title='Time Period'), 
            y=alt.Y('mean_ndvi:Q', title='Mean NDVI'),
            color='Period:N',
            column=alt.Column('land_cover:N', title='Land Cover Class', header=alt.Header(titleOrient="bottom", labelOrient="bottom")),
            tooltip=['land_cover', 'Period', 'mean_ndvi', 'pixel_count']
        ).properties(
            title='Mean NDVI by Land Cover Class: 2022 vs 2024',
            width=100
        )
        
    mo.vstack([
        mo.md("## Analysis Results"),
        chart if 'chart' in locals() else "",
        mo.md("### 2022-2023 Stats"), stats_22,
        mo.md("### 2024-2025 Stats"), stats_24
    ])
    return chart, s22, s24, viz_df


@app.cell
def _(
    CONFIG,
    Path,
    chart,
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
        chart.save(str(chart_path))
    except Exception as e:
        print(f"Could not save chart: {e}")

    # 2. Report
    report_content = f"""# Temporal Geospatial Analysis Report
    
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**AOI:** {CONFIG['geojson_path']}

## Executive Summary
Comparison of vegetation health (NDVI) across land cover classes between **2022-2023** and **2024-2025**.

## Results

### 2022-2023
{stats_22.to_pandas().to_markdown(index=False) if stats_22 is not None else "No Data"}

### 2024-2025
{stats_24.to_pandas().to_markdown(index=False) if stats_24 is not None else "No Data"}

![NDVI Comparison Chart](../figures/{chart_path.name})
"""
    report_path = reports_dir / f"temporal_report_{timestamp}.md"
    report_path.write_text(report_content)
    print(f"Report saved to: {report_path}")

    # 3. Create PyStac Items
    def save_stac(combined_ds, period_label, stats_df):
        if combined_ds is None: return
        
        # Define metadata directory
        metadata_dir = Path("../../data/metadata")
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
                "cecil:subscription_id": CONFIG['cecil_dataset_id']
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

    return (
        chart_path,
        figures_dir,
        output_dir,
        report_content,
        report_path,
        reports_dir,
        save_stac,
        timestamp,
    )


if __name__ == "__main__":
    app.run()
