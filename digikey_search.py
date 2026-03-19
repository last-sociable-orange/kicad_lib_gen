"""
The coding instructions in digikey_search.py outline the following steps:
1. The Digikey search API is defined in 'ProductSearch.json'. Input arguments include:
    'Keywords'
    'Limit' (default value 50)
    'FilterOptionsRequest'
    'SortOptions'
2. Read client credentials from .env file:
    client_id
    client_secret
    access_token
    refresh_token
3. Error handling:
    a. If a '401' response is received, request a new access token using the refresh_access_token() function defined in 'digikey_auth.py'. Update the .env file with the new access_token and refresh_token returned by this function.
    b. For other errors, print the error message to the screen.
4. Return search results in JSON format.
"""

import logging
import json
import datetime
from time import time
import os
import requests
import argparse
from digikey_auth import refresh_access_token


def digikey_search(keywords: str, token_file: str = ".token", limit=10, offset=0):

    # Check if default token file exists
    if token_file == ".token" and not os.path.exists(token_file):
        raise FileNotFoundError(
            "Authentication token not found. Please run digikey_auth.py to get a valid token"
        )

    with open(token_file, "r") as file:
        tokens = json.load(file)

    # load client info and tokens
    try:
        client_id = tokens["client_id"]
        client_secret = tokens["client_secret"]
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        expires_by = tokens["expires_by"]
        refresh_token_expires_by = tokens["refresh_token_expires_by"]
    except Exception as e:
        logging.error(f"Reading tokens error: {str(e)}")
        raise

    # check if token has expired
    # shall allow >30 seconds token life time otherwise refresh
    time_now = int(time())
    if (expires_by - time_now) < 30:
        # check if refresh token is valid
        if (refresh_token_expires_by - time_now) < 30:
            logging.error(
                "Refresh token has expired, use digikey_auth to get a new token"
            )
            raise Exception("Refresh token has expired")
        else:
            # update tokens and token file
            try:
                access_token, refresh_token, expires_in, refresh_token_expires_in = (
                    refresh_access_token(
                        client_id=client_id,
                        client_secret=client_secret,
                        refresh_token=refresh_token,
                    )
                )
                tokens["access_token"] = access_token
                tokens["refresh_token"] = refresh_token
                time_now = int(time())
                tokens["expires_by"] = time_now + expires_in
                tokens["refresh_token_expires_by"] = time_now + refresh_token_expires_in
                with open(token_file, "w") as file:
                    json.dump(tokens, file)
                logging.info(".token file updated")
            except Exception as e:
                logging.error(f"Failed to refresh token: {str(e)}")
                raise

    url = "https://api.digikey.com/products/v4/search/keyword"

    # Prepare request payload
    payload = {
        "Keywords": keywords,
        "Limit": limit,
        "Offset": offset,
        # 'FilterOptionsRequest': filter_options,
        # 'SortOptions': sort_options
    }

    headers = {
        "Accept": "application/json",
        "X-DIGIKEY-Client-Id": f"{client_id}",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Make the API request (placeholder URL)
    try:
        logging.debug("sending request...")
        response = requests.post(url, headers=headers, json=payload)
    except Exception as e:
        logging.error(f"Search request failed: {str(e)}")
        raise

    if response.status_code != 200:
        logging.error(
            f"Response status error: {response.status_code} - {response.text}"
        )
        raise Exception("Search rquest unsuccessful")

    return response.json()


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(description="Perform Digikey product search")
    parser.add_argument("keywords", type=str, help="Search keywords")
    parser.add_argument(
        "--limit", type=int, default=10, help="Maximum number of results"
    )
    parser.add_argument(
        "--offset", type=int, default=0, help="Index offset for paginate"
    )
    # parser.add_argument('--filters', type=str, help='Filter options as JSON string')
    # parser.add_argument('--sort', type=str, help='Sort options as JSON string')

    args = parser.parse_args()
    logging.debug(f"args:{args.keywords},{args.limit},{args.offset}")

    try:
        results = digikey_search(
            keywords=args.keywords,
            limit=args.limit,
            offset=args.offset,
            # filter_options=filters,
            # sort_options=sort
        )
        logging.debug("search done, saving to file...")
        current_time = datetime.datetime.now()
        # Format the timestamp as a string (e.g., "2023-10-05_14-30-00")
        timestamp = current_time.strftime("%m-%d_%H-%M-%S")
        # Define the filename with the timestamp
        filename = f"response_{timestamp}_{args.keywords.replace(' ', '_')}.json"

        with open(filename, "w") as file:
            json.dump(results, file, indent=2)

        for product in results["Products"]:
            logging.debug(
                f"Manufacturer:{product['Manufacturer']['Name']} - MPN: {product['ManufacturerProductNumber']}"
            )
    except json.JSONDecodeError:
        logging.error("Invalid JSON format")
        raise
    except Exception as e:
        logging.error(f"Search failed: {str(e)}")
        raise
