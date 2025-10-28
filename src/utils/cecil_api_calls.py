import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


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
def _(load_dotenv):
    load_dotenv()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Load Cecil Client""")
    return


@app.cell
def _(cecil):
    cecil_client = cecil.Client()
    return (cecil_client,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Area of Interest (AOI)""")
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
    print(aoi_colossus)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Land Cover 9-Class""")
    return


@app.cell
def _():
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# SBTN Natural Lands Dataset (2000)""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""The documentation for the _SBTN Natural Lands data_ can be found """)
    return


app._unparsable_cell(
    r"""
    sbtn_natural_lands_colossus = cecil_client.create_data_request(
        externel_ref=\"SBTN Natrual Lands - Colossus Data Center\"
        aoi_id=
        dataset_id='a4bb9aea-b6df-4d19-9083-38357f8fa76c' 
    )
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""#""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r""" """)
    return


if __name__ == "__main__":
    app.run()
