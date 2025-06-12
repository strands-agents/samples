'''
MIT No Attribution

Copyright 2024 Amazon Web Services

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''

import time
from datetime import datetime
from typing import Dict, Any
import random
import os
import requests
import json
from strands import tool


@tool
def get_site_info(site_id: str) -> str:
    """
    Get the entity hierarchy of a given site as a nested json.

    This function reads and returns the contents of the entity hierarchy file for a specified site.
    The type field in the result can be one of the following: <Building/Floor/Zone/Plant/TemperatureSensor/VAV/ChilledWaterPump/Chiller>

    Args:
        site_id (str): The unique identifier of the site to get information for. Example: 's123'

    Returns:
        str: The entity hierarchy data as a JSON string in the following FIXED format.
            '{
                "id": {"entityType": "<ASSET>/,<DEVICE>" , "id": "xxx"},
                "name": "xxx",
                "type": "<Building/Floor/Zone/Plant/TemperatureSensor/VAV/ChilledWaterPump/Chiller>",
                "label": "xxx",
                "children": [
                    {
                        "entity": {
                            "id": {"entityType": "<ASSET>/,<DEVICE>" , "id": "yyy"},
                            "name": "yyy",
                            "type": "yyy",
                            "label": "yyy",
                            "children": [
                            ]
                        }
                    },
                    {
                        "entity": {
                            "id": {"entityType": "<ASSET>/,<DEVICE>" , "id": "zzz"},
                            "name": "zzz",
                            "type": "zzz",
                            "label": "zzz",
                            "children": [
                            ]
                        }
                    }

                ]
            }'

    Example:
        >>> get_site_info('s123')
        '{
            "id": {"entityType": "ASSET", "id": "b5c24680-50f1-11ef-b4ce-d5aee9e495ad"},
            "name": "Office Building HVAC",
            "type": "Building",
            "children": [{
                "entity": {
                "id": {"entityType": "ASSET", "id": "b5c24681-50f1-11ef-b4ce-d5aee9e495ad"},
                "name": "Ground Floor",
                "type": "Floor",
                "children": [{
                    "entity": {
                    "id": {"entityType": "ASSET", "id": "gf-zone-1"},
                    "name": "GF-Zone-1",
                    "type": "Zone",
                    "children": [{
                        "entity": {
                        "id": {"entityType": "DEVICE", "id": "gf-ts-1"},
                        "name": "GF-TS-1",
                        "type": "TemperatureSensor",
                        "children": []
                        }
                    }, {
                        "entity": {
                        "id": {"entityType": "DEVICE", "id": "gf-vav-1"},
                        "name": "GF-VAV-1",
                        "type": "VAV",
                        "children": []
                        }
                    }]
                    }
                }]
                // ... GF-Zone-2 through GF-Zone-5 follow same pattern
                }
            }, {
                "entity": {
                "id": {"entityType": "ASSET", "id": "b5c24682-50f1-11ef-b4ce-d5aee9e495ae"},
                "name": "First Floor",
                "type": "Floor",
                "children": [{
                    "entity": {
                    "id": {"entityType": "ASSET", "id": "f1-zone-1"},
                    "name": "F1-Zone-1",
                    "type": "Zone",
                    "children": [{
                        "entity": {
                        "id": {"entityType": "DEVICE", "id": "f1-ts-1"},
                        "name": "F1-TS-1",
                        "type": "TemperatureSensor",
                        "children": []
                        }
                    }, {
                        "entity": {
                        "id": {"entityType": "DEVICE", "id": "f1-vav-1"},
                        "name": "F1-VAV-1",
                        "type": "VAV",
                        "children": []
                        }
                    }]
                    }
                }]
                // ... F1-Zone-2 through F1-Zone-10 follow same pattern
                }
            }, {
                "entity": {
                "id": {"entityType": "ASSET", "id": "b5c24682-50f2-11ef-b4ce-d5aee9e495ae"},
                "name": "Second Floor",
                "type": "Floor",
                "children": [{
                    "entity": {
                    "id": {"entityType": "ASSET", "id": "f2-zone-1"},
                    "name": "F2-Zone-1",
                    "type": "Zone",
                    "children": [{
                        "entity": {
                        "id": {"entityType": "DEVICE", "id": "f2-ts-1"},
                        "name": "F2-TS-1",
                        "type": "TemperatureSensor",
                        "children": []
                        }
                    }, {
                        "entity": {
                        "id": {"entityType": "DEVICE", "id": "f2-vav-1"},
                        "name": "F2-VAV-1",
                        "type": "VAV",
                        "children": []
                        }
                    }]
                    }
                }]
                // ... F2-Zone-2 through F2-Zone-10 follow same pattern
                }
            }, {
                "entity": {
                "id": {"entityType": "ASSET", "id": "b5c24682-50f1-11ef-b4ce-d5aee9e495ad"},
                "name": "Mechanical Plant",
                "type": "Plant",
                "children": [{
                    "entity": {
                    "id": {"entityType": "DEVICE", "id": "ahu-1"},
                    "name": "AHU-1",
                    "type": "AirHandlingUnit",
                    "children": []
                    }
                }, {
                    "entity": {
                    "id": {"entityType": "DEVICE", "id": "chiller-1"},
                    "name": "Chiller-1",
                    "type": "Chiller",
                    "children": []
                    }
                }, {
                    "entity": {
                    "id": {"entityType": "DEVICE", "id": "chwp-1"},
                    "name": "CHWP-1",
                    "type": "ChilledWaterPump",
                    "children": []
                    }
                }]
                // ... AHU-2, AHU-3, CHWP-2 follow same pattern
                }
            }]
            }'
    
    """
    
    ID_TOKEN = os.environ.get('ID_TOKEN', '')
    TOOL_API_ENDPOINT = os.environ.get('TOOL_API_ENDPOINT', '')
    if ID_TOKEN != "":
        #invoke the HTTP GET API to get the site info
        headers = {
            'id_token': ID_TOKEN
        }
        response = requests.get(TOOL_API_ENDPOINT + '/entities', headers=headers)
        return response.text
    else:
        return '{}'



@tool
def get_timeseries_data(entity_id: str, property: str, start_time: str, end_time: str) -> Dict[str, Any]:
    """
    Get timeseries data for a specific entity and property within a given time range.

    This function retrieves time-series values for a specified property of an entity
    within the provided time window.

    Args:
        entity_id (str): Unique identifier for the entity. Example: "0e4b4070-50ff-11ef-b4ce-d5aee9e495ad" this is NOT the name like "Inverter5"
        property (str): Name of the property to retrieve values for. Example: "power"
        start_time (str): Start date time string for the data range
        end_time (str): End date time string for the data range

    Returns:
        dict: Dictionary containing timeseries data in the format:
            {
                "data": [
                    {"time": timestamp, "value": numeric_value},
                    ...
                ]
            }

    Example:
        >>> get_timeseries_data("12345", "power", "2024-01-01 00:00:00", "2024-01-02 23:59:59")
        {
            "data": [
                {"time": 1739325219, "value": 5.5},
                {"time": 1739325219, "value": 6.5},
                {"time": 1739325219, "value": 7.5},
                {"time": 1739325219, "value": 8.0}
            ]
        }
    """

    ID_TOKEN = os.environ.get('ID_TOKEN', '')
    TOOL_API_ENDPOINT = os.environ.get('TOOL_API_ENDPOINT', '')
    if ID_TOKEN != "":
        #invoke the HTTP GET API to get the site info
        headers = {
            'id_token': ID_TOKEN
        }
        params = {
            'entity_id': entity_id,
            'property': property,
            'start_time': start_time,
            'end_time': end_time
        }

        response = requests.get(
            TOOL_API_ENDPOINT + '/timeseries',
            headers=headers,
            params=params
        )
        return json.loads(response.text)
    else:
        return {
            "data": []
        }
    
    
       
