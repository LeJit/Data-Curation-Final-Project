import cecil
from dotenv import load_dotenv
import os
import json
from pathlib import Path
from typing import List, Dict

load_dotenv()

# Dictionary mapping Dataset Name to Cecil Dataset ID
CECIL_DATASETS = {
    "Land Cover 9-Class": "a4bb9aea-b6df-4d19-9083-38357f8fa76c",
    "SBTN Natural Lands": "bf249342-557a-4028-922c-c67fc4ad6a64"
}

def parse_subscription(subscription) -> Dict:
    """
    Parse a Cecil Subscription object into a dictionary with relevant attributes
    for future processing.

    Parameters
    ==========
    subscription: cecil.Subscription
        The Cecil Subscription object to parse.

    Returns
    =======
    dict
        A dictionary with relevant attributes of the subscription.
    """
    return {
        "id": subscription.id,
        "name": subscription.external_ref,
        "dataset_id": subscription.dataset_id,
        "aoi_id": subscription.aoi_id
    }

def create_subscriptions(client: cecil.Client, aoi_id: str) -> List[Dict]:
    """
    Create Cecil Subscriptions for the given AOI and save them to a JSON file.

    Parameters
    ==========
    client: cecil.Client
        The Cecil Client to use for creating the Subscriptions.
    aoi_id: str
        The ID of the AOI to create Subscriptions for.

    Returns
    =======
    list[dict]
        The list of Cecil Subscriptions created.
    """
    subscriptions = []
    for dataset_name, dataset_id in CECIL_DATASETS.items():
        subscription = client.create_subscription(
            aoi_id=aoi_id,
            dataset_id=dataset_id,
            external_ref=dataset_name
        )
        subscriptions.append(parse_subscription(subscription))
    return subscriptions

def create_aoi(client: cecil.Client, geometry: dict):
    """
    Create an Area of Interest (AOI) using the Cecil API.

    Parameters
    ==========
    client: cecil.Client
        The Cecil Client to use for creating the AOI.
    geometry: dict
        The geometry of the AOI in GeoJSON format.

    Returns
    =======
    cecil.AOI
        The created AOI.
    """
    aoi = client.create_aoi(
        external_ref="Colossus Data Center",
        geometry=geometry
    )
    return aoi


def save_subscriptions(subscriptions: List[Dict]):
    """
    Save a list of Cecil Subscriptions to a JSON file.

    Parameters
    ==========
    subscriptions: list[dict]
        The list of Cecil Subscriptions to save.
    """
    with open("data/processed/cecil_subscriptions.json", "w") as f:
        json.dump(subscriptions, f, indent=4)

def main():
    # Set Up Cecil Client
    client = cecil.Client()
    
    # Create AOI
    with open("data/colossus.json") as f:
        colossus_geojson = json.load(f)
    colossus_geometry = colossus_geojson.get("features")[0].get("geometry")
    aoi = create_aoi(client, colossus_geometry)
    
    # Create Subscriptions
    subscriptions = create_subscriptions(client, aoi.id)
    
    # Save Subscriptions
    save_subscriptions(subscriptions)

if __name__ == "__main__":
    main()

    