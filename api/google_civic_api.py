import requests
import os

def get_representatives(address=None, levels=None, roles=None):
    base_url = "https://www.googleapis.com/civicinfo/v2/representatives"
    api_key = os.environ.get('GOOGLE_API_KEY')  # Fetch the API key from environment variables
    if not api_key:
        raise ValueError("No Google Civic Information API key found in environment variables")

    params = {
        'key': api_key,
        'address': address,
        'levels': levels,
        'roles': roles
    }

    # Filter out None values
    params = {k: v for k, v in params.items() if v is not None}

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to retrieve data', 'status_code': response.status_code}
