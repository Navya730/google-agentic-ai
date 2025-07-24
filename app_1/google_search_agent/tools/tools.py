import requests
def get_agriculture_data(state:str) -> dict:
    """
    Retrieves the current mandi price for a given state.

    Args:
        state (str): name of the state (e.g., "Himachal Pradesh", "Haryana").

    Returns:
        dict: mandi prices.
    """
    base_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    api_key = "579b464db66ec23bdd0000010d6ee01ef041400b6f72a216df7da280"

    params = {
        "api-key": api_key,
        "format": "json",
        "state": state
    }
    print("============",state)

    try:
        response = requests.get(base_url, params=params)
        print("================",response)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx, 5xx)

        data = response.json()
        return data.get("records", [])  # Return list of mandi records

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for state '{state}': {e}")
        return None
