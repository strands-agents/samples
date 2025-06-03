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
from io import StringIO
import os
import boto3
import json
import sys
from datetime import datetime
import random
from typing  import Dict, Any
from strands import tool

@tool
def get_current_time(timezone: str) -> Dict[str, Any]:
    """
    Gets the current time in both Unix timestamp and ISO format.

    This function returns the current time in two formats:
    1. Unix timestamp (seconds since epoch)
    2. ISO formatted date-time string in local timezone
    
    Args:
        timezone (str): timezone eg: UTC+05:30
        
    Returns:
        dict: A dictionary containing two keys:
            - 'time' (int): Unix timestamp in seconds since epoch
            - 'iso_time' (str): Formatted date-time string in 'YYYY-MM-DD HH:MM:SS' format

    Example:
        >>> result = get_current_time()
        >>> print(result)
        {
            'time': 1704891234,
            'iso_time': '2024-01-10 14:27:14'
        }

    Note:
        - The Unix timestamp is returned as an integer (seconds since January 1, 1970)
        - The ISO time string uses the local system timezone
        - The time format used is 24-hour clock
    """

    #return unix timestamp and iso date time string
    return {
                "time": int(time.time()), 
                "iso_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }







