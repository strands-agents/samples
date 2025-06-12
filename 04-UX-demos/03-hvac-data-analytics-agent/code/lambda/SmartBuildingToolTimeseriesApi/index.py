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
import json

#This is a dummy API which will return a set of random timeseries data
def lambda_handler(event, context):

    
    end_time =  event['queryStringParameters']['end_time']
    entity_id =  event['queryStringParameters']['entity_id']
    property_name =  event['queryStringParameters']['property']
    start_time =  event['queryStringParameters']['start_time'] 

    # Convert string times to timestamps
    start_ts = int(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").timestamp())
    end_ts = int(datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").timestamp())
    
    # Generate data points every 10 minutes
    interval = 600  # 10 minutes in seconds
    data = []
    
    current_ts = start_ts
    while current_ts <= end_ts:
        data.append({
            "time": current_ts,
            "value": round(random.uniform(18, 24), 2)
        })
        current_ts += interval
        
    return json.dumps({
        "data" : data
    })