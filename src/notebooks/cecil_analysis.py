import marimo

__generated_with = "0.18.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import cecil
    import json
    import os
    import xarray as xr
    from dotenv import load_dotenv

    load_dotenv()
    return cecil, json, mo


@app.cell
def _(mo):
    mo.md(r"""
    # Cecil Data Analysis

    This notebook analyzes the Cecil subscriptions found in `../../data/processed/cecil_subscriptions.json`.
    """)
    return


@app.cell
def _(cecil):
    client = cecil.Client()
    return (client,)


@app.cell
def _(json, mo):
    with open("../../data/processed/cecil_subscriptions.json", "r") as f:
        subscriptions = json.load(f)

    mo.md(f"Loaded {len(subscriptions)} subscriptions from `../../data/processed/cecil_subscriptions.json`.")
    return (subscriptions,)


@app.cell
def _(client, subscriptions):
    results = []

    for sub in subscriptions:
        sub_id = sub["id"]
        sub_name = sub.get("name", "Unknown")
        dataset_id = sub.get("dataset_id")

        try:
            # We use the 'id' from the subscription JSON as the subscription_id for load_xarray
            ds = client.load_xarray(subscription_id=sub_id)

            summary = {
                "name": sub_name,
                "id": sub_id,
                "dataset_id": dataset_id,
                "dims": dict(ds.sizes),
                "data_vars": list(ds.data_vars.keys()),
                "coords": list(ds.coords.keys()),
                "stats": {}
            }
            print(summary)

            # Calculate basic stats for each data variable
            results.append((sub, ds, summary))

        except Exception as e:
            results.append((sub, None, {"error": str(e)}))
    return (ds,)


@app.cell
def _():
    return


@app.cell
def _():
    return


@app.cell
def _(ds, mo):
    # First, let's explore the dataset structure in detail
    mo.md(f"""
    ## Dataset Structure

    **Dimensions:** {dict(ds.sizes)}

    **Coordinates:** {list(ds.coords.keys())}

    **Data Variables:** {list(ds.data_vars.keys())}
    """)
    return


@app.cell
def _():
    return


@app.cell
def _(ds):
    # Display detailed information about each variable
    var_info = []
    for var_name in ds.data_vars:
        da = ds[var_name]
        var_info.append({
            "Variable": var_name,
            "Dimensions": str(da.dims),
            "Shape": str(da.shape),
            "Data Type": str(da.dtype),
            "Description": da.attrs.get("long_name", "N/A")
        })

    import polars as pl
    var_df = pl.DataFrame(var_info)
    var_df
    return (pl,)


@app.cell
def _():
    return


@app.cell
def _(ds, mo, pl):
    # Extract the natural lands data
    # Based on SBTN Natural Lands documentation, this should contain binary classification
    natural_lands = ds['binary_class']

    # Convert to numpy for analysis
    natural_data = natural_lands.values

    # Calculate statistics
    total_pixels = natural_data.size
    natural_pixels = (natural_data == 1).sum()
    non_natural_pixels = (natural_data == 0).sum()
    unknown_pixels = total_pixels - natural_pixels - non_natural_pixels

    stats_df = pl.DataFrame({
        "Category": ["Natural", "Non-Natural", "Unknown/No Data"],
        "Pixels": [int(natural_pixels), int(non_natural_pixels), int(unknown_pixels)],
        "Percentage": [
            100 * natural_pixels / total_pixels,
            100 * non_natural_pixels / total_pixels,
            100 * unknown_pixels / total_pixels
        ]
    })

    mo.vstack([
        mo.md("## Land Usage Statistics"),
        stats_df
    ])
    return natural_data, stats_df


@app.cell
def _(pl, stats_df):
    import altair as alt

    # Create a pie chart showing natural vs non-natural land
    pie_chart = alt.Chart(stats_df.filter(pl.col("Pixels") > 0)).mark_arc(innerRadius=50).encode(
        theta=alt.Theta(field="Pixels", type="quantitative"),
        color=alt.Color(
            field="Category",
            type="nominal",
            scale=alt.Scale(
                domain=["Natural", "Non-Natural", "Unknown/No Data"],
                range=["#2d7f3e", "#c44e52", "#cccccc"]
            ),
            legend=alt.Legend(title="Land Type")
        ),
        tooltip=[
            alt.Tooltip("Category:N", title="Type"),
            alt.Tooltip("Pixels:Q", title="Pixels", format=","),
            alt.Tooltip("Percentage:Q", title="Percentage", format=".2f")
        ]
    ).properties(
        title="Memphis Land Usage Distribution (2000)",
        width=400,
        height=400
    )

    pie_chart
    return alt, pie_chart


@app.cell
def _():
    return


@app.cell
def _(alt, pl, stats_df):
    # Create a bar chart for easier comparison
    bar_chart = alt.Chart(stats_df.filter(pl.col("Pixels") > 0)).mark_bar().encode(
        x=alt.X("Category:N", title="Land Type", sort=None),
        y=alt.Y("Percentage:Q", title="Percentage of Total Area (%)", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color(
            "Category:N",
            scale=alt.Scale(
                domain=["Natural", "Non-Natural", "Unknown/No Data"],
                range=["#2d7f3e", "#c44e52", "#cccccc"]
            ),
            legend=None
        ),
        tooltip=[
            alt.Tooltip("Category:N", title="Type"),
            alt.Tooltip("Percentage:Q", title="Percentage", format=".2f")
        ]
    ).properties(
        title="Natural vs Non-Natural Land Usage Comparison",
        width=400,
        height=300
    )

    bar_chart
    return (bar_chart,)


@app.cell
def _(natural_data):
    natural_data_reshaped = natural_data.reshape((40,44))
    return (natural_data_reshaped,)


@app.cell
def _(alt, ds, natural_data_reshaped, pl):
    # Create a spatial heatmap visualization
    import numpy as np

    # Prepare data for visualization
    y_coords = ds.coords['y'].values
    x_coords = ds.coords['x'].values

    # Create a dataframe with coordinates and values
    spatial_data = []
    for i, y in enumerate(y_coords):
        for j, x in enumerate(x_coords):
            value = float(natural_data_reshaped[i, j])
            if not np.isnan(value):
                spatial_data.append({
                    "x": float(x),
                    "y": float(y),
                    "natural": "Natural" if value == 1 else "Non-Natural"
                })

    spatial_df = pl.DataFrame(spatial_data)

    # Create spatial visualization
    spatial_viz = alt.Chart(spatial_df).mark_square(size=100).encode(
        x=alt.X('x:Q', title='Longitude', scale=alt.Scale(zero=False)),
        y=alt.Y('y:Q', title='Latitude', scale=alt.Scale(zero=False)),
        color=alt.Color(
            'natural:N',
            scale=alt.Scale(
                domain=["Natural", "Non-Natural"],
                range=["#2d7f3e", "#c44e52"]
            ),
            legend=alt.Legend(title="Land Type")
        ),
        tooltip=['x:Q', 'y:Q', 'natural:N']
    ).properties(
        title='Spatial Distribution of Natural vs Non-Natural Land (Memphis, TN - 2000)',
        width=600,
        height=500
    )

    spatial_viz
    return (spatial_viz,)


@app.cell
def _(mo):
    mo.md(r"""
    # Save Report
    """)
    return


@app.cell
def _(pl):
    from pathlib import Path
    from datetime import datetime

    def generate_markdown_template(
        dataset,
        stats_dataframe: pl.DataFrame,
        natural_data_array
    ) -> str:
        """
        Generate Markdown content for the land usage report.
    
        Args:
            dataset: xarray Dataset containing the natural lands data
            stats_dataframe: Polars DataFrame with land usage statistics
            natural_data_array: numpy array with the natural lands data values
        
        Returns:
            Markdown-formatted string containing the complete report
        """
        # Extract statistics
        natural_stats = stats_dataframe.filter(pl.col("Category") == "Natural")
        non_natural_stats = stats_dataframe.filter(pl.col("Category") == "Non-Natural")
    
        natural_pct = natural_stats["Percentage"][0] if len(natural_stats) > 0 else 0
        non_natural_pct = non_natural_stats["Percentage"][0] if len(non_natural_stats) > 0 else 0
        natural_pixels = natural_stats["Pixels"][0] if len(natural_stats) > 0 else 0
        non_natural_pixels = non_natural_stats["Pixels"][0] if len(non_natural_stats) > 0 else 0
    
        # Get dataset metadata
        total_pixels = natural_data_array.size
        spatial_resolution = abs(float(dataset.coords['x'][1] - dataset.coords['x'][0]))
    
        # Generate report content
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
        markdown_content = f"""# Memphis, Tennessee Land Usage Analysis Report
    ## Year 2000 - Natural vs Non-Natural Lands

    **Report Generated:** {report_date}  
    **Data Source:** SBTN Natural Lands Dataset  
    **Documentation:** https://docs.cecil.earth/SBTN-Natural-Lands-232ef16bbbe48000868ed8c4c82cc8ce

    ---

    ## Executive Summary

    This report analyzes land usage patterns in Memphis, Tennessee for the year 2000, classifying areas as either natural or non-natural based on the Science Based Targets Network (SBTN) Natural Lands criteria.

    ### Key Findings

    - **Total Area Analyzed:** {total_pixels:,} pixels
    - **Spatial Resolution:** ~{spatial_resolution:.4f} degrees
    - **Natural Land Coverage:** {natural_pct:.2f}% ({natural_pixels:,} pixels)
    - **Non-Natural Land Coverage:** {non_natural_pct:.2f}% ({non_natural_pixels:,} pixels)

    ---

    ## Methodology

    The analysis uses the SBTN Natural Lands dataset, which classifies land areas based on:
    - Minimal human modification
    - Ecosystem integrity
    - Natural vegetation cover
    - Land use intensity

    According to SBTN criteria:
    - **Natural Lands (value = 1):** Areas with minimal human impact, maintaining natural ecosystems
    - **Non-Natural Lands (value = 0):** Areas significantly modified by human activity, including urban development, agriculture, and infrastructure

    ---

    ## Results

    ### Overall Land Distribution

    | Category | Pixels | Percentage |
    |----------|--------|------------|
    | Natural | {natural_pixels:,} | {natural_pct:.2f}% |
    | Non-Natural | {non_natural_pixels:,} | {non_natural_pct:.2f}% |

    ### Proportional Distribution

    ![Land Usage Pie Chart](figures/land_usage_pie.png)

    *Figure 1: Proportional distribution of natural versus non-natural land in Memphis, TN (2000)*

    ### Comparative Analysis

    ![Land Usage Bar Chart](figures/land_usage_bar.png)

    *Figure 2: Direct comparison of natural and non-natural land percentages*

    ### Spatial Distribution

    ![Spatial Distribution Map](figures/spatial_distribution.png)

    *Figure 3: Geographic distribution of natural (green) and non-natural (red) lands across the study area*

    ---

    ## Interpretation

    ### Urban Development Impact

    With {non_natural_pct:.2f}% of the analyzed area classified as non-natural, Memphis shows {'significant' if non_natural_pct > 50 else 'moderate'} human modification of the landscape. This is {'consistent with' if non_natural_pct > 50 else 'lower than expected for'} a major urban center.

    ### Natural Land Preservation

    The {natural_pct:.2f}% natural land coverage indicates {'limited' if natural_pct < 30 else 'moderate' if natural_pct < 50 else 'substantial'} preservation of natural ecosystems within or near the urban area. This may include:
    - Riparian zones along the Mississippi River
    - Protected green spaces and parks
    - Undeveloped peripheral areas
    - Forest remnants

    ### Spatial Patterns

    The spatial distribution map reveals:
    - {'Concentrated' if non_natural_pct > 60 else 'Distributed'} patterns of urban development
    - {'Fragmented' if natural_pct < 40 else 'Connected'} natural land areas
    - Potential corridors for wildlife and ecosystem services

    ---

    ## Conclusions

    1. **Land Use Balance:** Memphis exhibited a {natural_pct:.2f}% to {non_natural_pct:.2f}% ratio of natural to non-natural land in 2000.

    2. **Conservation Implications:** The {'limited' if natural_pct < 30 else 'moderate'} natural land coverage suggests {'urgent need for' if natural_pct < 30 else 'opportunities for'} conservation efforts to maintain ecosystem services.

    3. **Urban Planning:** Understanding this baseline from 2000 is crucial for:
       - Tracking land use change over time
       - Identifying areas for restoration
       - Planning sustainable urban growth
       - Setting conservation targets

    ---

    ## Data Specifications

    **Dataset Details:**
    - **Dimensions:** {dict(dataset.sizes)}
    - **Coordinate System:** Geographic (latitude/longitude)
    - **Data Type:** Binary classification (0/1)
    - **Coverage Area:** Memphis, Tennessee region

    **Quality Notes:**
    - Data represents year 2000 land classification
    - Classification based on SBTN Natural Lands methodology
    - Spatial resolution: ~{spatial_resolution:.4f} degrees

    ---

    ## References

    1. Science Based Targets Network (SBTN) Natural Lands Documentation:  
       https://docs.cecil.earth/SBTN-Natural-Lands-232ef16bbbe48000868ed8c4c82cc8ce

    2. Analysis Date: {report_date}

    ---

    ## Appendix: Statistical Summary

    Total Pixels: {total_pixels:,} Natural Pixels: {natural_pixels:,} ({natural_pct:.2f}%) Non-Natural Pixels: {non_natural_pixels:,} ({non_natural_pct:.2f}%) Spatial Resolution: {spatial_resolution:.4f} degrees


    ---

    *Report generated automatically using Python geospatial analysis tools*
    """
        return markdown_content
    return Path, datetime, generate_markdown_template


@app.cell
def _(Path, alt, datetime):
    def save_report_and_figures(
        markdown_content: str,
        charts: dict[str, alt.Chart],
        output_dir: str = "outputs"
    ) -> Path:
        """
        Save the Markdown report and associated chart figures to disk.
    
        Args:
            markdown_content: Complete Markdown-formatted report content
            charts: Dictionary mapping chart names to Altair chart objects
                Expected keys: 'pie', 'bar', 'spatial'
            output_dir: Directory to save the report and figures
        
        Returns:
            Path to the generated Markdown file
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
        # Create figures subdirectory
        figures_path = output_path / "figures"
        figures_path.mkdir(exist_ok=True)
    
        # Save all charts as PNG files
        chart_files = {
            'pie': figures_path / "land_usage_pie.png",
            'bar': figures_path / "land_usage_bar.png",
            'spatial': figures_path / "spatial_distribution.png"
        }
    
        for chart_name, chart_obj in charts.items():
            if chart_name in chart_files:
                chart_obj.save(str(chart_files[chart_name]))
    
        # Generate timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = output_path / f"memphis_land_usage_report_{timestamp}.md"
    
        # Save report to file
        report_file.write_text(markdown_content)
    
        return report_file
    return (save_report_and_figures,)


@app.cell
def _(
    bar_chart,
    ds,
    generate_markdown_template,
    mo,
    natural_data,
    pie_chart,
    save_report_and_figures,
    spatial_viz,
    stats_df,
):
    # Generate the report using both functions
    markdown_report = generate_markdown_template(ds, stats_df, natural_data)

    charts_dict = {
        'pie': pie_chart,
        'bar': bar_chart,
        'spatial': spatial_viz
    }

    _report_path = save_report_and_figures(markdown_report, charts_dict)

    mo.md(f"""
    ## Report Generated Successfully! ✅

    **Report saved to:** `{_report_path}`

    **Additional files created:**
    - Pie chart: `{_report_path.parent}/figures/land_usage_pie.png`
    - Bar chart: `{_report_path.parent}/figures/land_usage_bar.png`
    - Spatial map: `{_report_path.parent}/figures/spatial_distribution.png`

    You can open the Markdown file in any text editor or Markdown viewer to see the complete report with all figures and analysis.
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
