import cecil
from dotenv import load_dotenv
import os
import json
from pathlib import Path

load_dotenv()

# Dictionary mapping Dataset Name to Cecil Dataset ID
CECIL_DATASETS = {
    "Land Cover 9-Class": "a4bb9aea-b6df-4d19-9083-38357f8fa76c",
    "SBTN Natural Lands": "bf249342-557a-4028-922c-c67fc4ad6a64"
}

def parse_subscription(subscription: cecil.Subscription) -> dict:
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
        "name": subscription.name,
        "dataset_id": subscription.dataset_id,
        "aoi_id": subscription.aoi_id,
    }
    