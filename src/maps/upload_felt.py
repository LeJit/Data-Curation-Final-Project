import os
import tempfile
import felt_python
import xarray as xr
import rioxarray
from dotenv import load_dotenv

load_dotenv()

def upload_xarray_to_felt(dataset: xr.DataArray, map_title: str, api_token: str = None) -> str:
    """
    Uploads an Xarray DataArray to Felt as a raster layer.

    Args:
        dataset (xr.DataArray): The geospatial data to upload. Must have geospatial coordinates.
        map_title (str): Title for the new map on Felt.
        api_token (str, optional): Felt API token. If None, checks FELT_ACCESS_TOKEN env var.

    Returns:
        str: The URL of the created map.
    """
    
    if api_token is None:
        api_token = os.environ.get("FELT_ACCESS_TOKEN")
        if not api_token:
            raise ValueError("FELT_ACCESS_TOKEN not found in environment variables or arguments.")

    # Create a temporary file to save the raster
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp_file:
        temp_path = tmp_file.name
    
    try:
        # Ensure CRS is set (if not already) - assuming inputs might be properly georeferenced
        print(f"Exporting Xarray dataset to temporary GeoTIFF: {temp_path}")
        dataset.rio.to_raster(temp_path)

        print(f"Creating new map on Felt: '{map_title}'")
        # Create map
        map_details = felt_python.create_map(title=map_title, api_token=api_token)
        
        # Handle response type (id might be an attribute or dict key)
        if hasattr(map_details, 'id'):
            map_id = map_details.id
            map_url = map_details.url
        else:
            map_id = map_details['id']
            map_url = map_details['url']

        print(f"Uploading file to Felt map {map_id}...")
        # Upload the raster file
        felt_python.upload_file(
            map_id=map_id,
            file_name=temp_path,
            layer_name=dataset.name or "Raster Layer",
            api_token=api_token
        )
        
        print(f"Upload initiated successfully. Map URL: {map_url}")
        return map_url

    except Exception as e:
        print(f"An error occurred during Felt upload: {e}")
        raise
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"Temporary file {temp_path} removed.")
