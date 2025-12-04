import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


app._unparsable_cell(
    r"""
    # Initialization code that runs before all other cells
    def create_cecil_api_call(client: cecil.Client, dataset_id: str, dataset_name: str, aoi_id: str):
    
    """,
    name="setup"
)


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    from dotenv import load_dotenv
    return (load_dotenv,)


@app.cell
def _():
    import os
    import json
    from pathlib import Path
    return (json,)


@app.cell
def _():
    import cecil
    return (cecil,)


@app.cell
def _():
    import xarray
    return


@app.cell
def _(load_dotenv):
    load_dotenv()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Load Cecil Client
    """)
    return


@app.cell
def _(cecil):
    cecil_client = cecil.Client()
    return (cecil_client,)


@app.cell
def _():
    CECIL_DATASETS = {
        "SBTN - Colossus": 'bf249342-557a-4028-922c-c67fc4ad6a64',
        "Impact Observation - Colossus": 'a4bb9aea-b6df-4d19-9083-38357f8fa76c'
    }
    return


@app.cell
def _():
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Area of Interest (AOI)
    """)
    return


@app.cell
def _(json):
    with open("data/colossus.json") as f:
        colossus_geojson = json.load(f)
    colossus_geojson
    return (colossus_geojson,)


@app.cell
def _(colossus_geojson):
    colossus_geometry = colossus_geojson.get("features")[0].get("geometry")
    colossus_geometry
    return (colossus_geometry,)


@app.cell
def _(cecil_client, colossus_geometry):
    aoi_colossus = cecil_client.create_aoi(
        external_ref="Colossus Data Center",
        geometry=colossus_geometry
    )
    return (aoi_colossus,)


@app.cell
def _(aoi_colossus):
    aoi_id_ = aoi_colossus.id
    print(aoi_colossus)
    return (aoi_id_,)


@app.cell
def _():
    return


@app.cell
def _():
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # SBTN Natural Lands Dataset (2000)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The documentation for the _SBTN Natural Lands data_ can be found
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Impact Observatory - Land Cover 9-Class
    """)
    return


@app.cell
def _(aoi_id_, cecil_client):
    sbtn_natural_lands_colossus = cecil_client.create_subscription(
        aoi_id=aoi_id_,
        dataset_id='a4bb9aea-b6df-4d19-9083-38357f8fa76c',
        external_ref="SBTN - Colossus"
    )
    return (sbtn_natural_lands_colossus,)


@app.cell
def _(sbtn_natural_lands_colossus):
    sbtn_sub_id_ = sbtn_natural_lands_colossus.id
    return (sbtn_sub_id_,)


@app.cell
def _(cecil_client, sbtn_sub_id_):
    sbtn_dataset = cecil_client.load_xarray(sbtn_sub_id_)
    return (sbtn_dataset,)


@app.cell
def _(sbtn_dataset):
    sbtn_dataset
    return


@app.cell
def _():
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
 
    """)
    return


if __name__ == "__main__":
    app.run()
