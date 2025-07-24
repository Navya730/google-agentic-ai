import requests
def get_farmer_info(userid:str) -> dict:
    """
    Retrieves the farmer information from the data store.

    Args:
        userid (str): nuser id

    Returns:
        dict: farmer information.
    """

    # API endpoint
    url = "https://gah-backend-2-675840910180.europe-west1.run.app/api/farmer/profile"

    # Bearer token
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0LCJleHAiOjE3NTM0MjgzMDR9.NXp14pbHuXtNir06GAD8FIZNX-KonDxdECt7o8X2A8Q"
    }

    # Make GET request
    response = requests.get(url, headers=headers)

    # Check response
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return {}

