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
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJleHAiOjE3NTM0NjE4MzZ9.n7D-69tEOmt1e-8ddptbAhcoSX7-2X3cFQ766plSJhE"
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

