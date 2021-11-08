"""
Unofficial Fiverr API helps you to get:

* Seller details
* Seller gigs
* Seller reviews
    * Group by buyers
    * Filter by Impression
    * Sort by time
    * Limit no. of reviews
"""

from typing import Union
from enum import Enum
import json
import re

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import requests

DESCRIPTION = __doc__ or ""
tags_metadata = [
    {
        "name": "Home"
    },
    {
        "name": "Seller Details",
        "description": "Get details about seller"
    },
]

app = FastAPI(
    title="Unofficial Fiverr API",
    description=DESCRIPTION,
    version="1.2",
    contact={
        "name": "Salman Shaikh",
        "url": "https://salmannotkhan.github.io/",
        "email": "tony903212@gmail.com"
    },
    openapi_tags=tags_metadata
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


class FilterBy(str, Enum):
    """
    Filter by Enum Class
    """
    POSITIVE = "positive"
    NEGATIVE = "negative"


class SortBy(str, Enum):
    """
    Sort by Enum Class
    """
    RECENT = "recent"
    RELEVANT = "relevant"


headers = {
    "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Upgrade-Insecure-Requests": "1",
    "TE": "trailers"
}
reviews_headers = {
    "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json",
    "Upgrade-Insecure-Requests": "1",
    "TE": "trailers"
}

def get_user_data(username: str):
    """
    Get basic seller details and CSRF Token
    """
    session = requests.Session()
    data_regex = r'(?<=perseusApp.initialData = ).+(?=;)'
    seller_url = f"https://www.fiverr.com/{username}"
    data = session.get(seller_url, headers=headers)
    react_data = re.findall(data_regex, data.text)[0]
    seller_data = json.loads(react_data)
    return session, seller_data


@app.get("/", tags=["Home"])
async def index():
    """
    Home Path for API
    """
    return {
        "Welcome to": "Unofficial Fiverr API",
        "For docs": "Visit /docs",
        "For redocs": "Visit /redoc",
    }


@app.get("/{username}", tags=["Seller Details"])
async def get_seller_details(username: str):
    """
    Remove unnecessary details from seller card and returns it
    """
    session, user_data = get_user_data(username)
    seller_card = user_data["userData"]["seller_card"]
    seller_profile = user_data["userData"]["seller_profile"]
    seller_card.update(seller_profile)
    seller_card.pop("biEventData")
    seller_card.pop("collectProps")
    seller_card.pop("identities")
    seller_card.pop("currency")
    seller_card.pop("abTests")
    session.close()
    return seller_card


@app.get("/{username}/gigs", tags=["Seller Details"])
async def get_gigs(username: str):
    """
    Get seller gigs
    """
    session, user_data = get_user_data(username)
    session.close()
    return user_data["gigs"]["gigs"]


@app.get("/{username}/reviews", tags=["Seller Details"])
async def get_reviews(username: str, filter_by: Union[FilterBy, None] = None,
                      sort_by: Union[SortBy, None] = None, group_by_buyer: bool = False,
                      limit: int = 9999):
    """
    Get seller reviews
    """
    url = "https://www.fiverr.com/ratings/index"
    session, user_data = get_user_data(username)

    # Adding CSRF Token
    reviews_headers["X-CSRF-Token"] = user_data["requestContext"]["csrf_token"]
    # Setting up payload
    payload: dict[str, str] = {}
    payload["user_id"] = user_data["userData"]["user"]["id"]
    if filter_by:
        payload["filter_by"] = filter_by.value
    if sort_by:
        payload["sort_by"] = sort_by.value
    reviews: list[dict[str, str]] = []

    while True:
        data = session.get(url, headers=headers, data=payload)
        data = data.json()
        reviews.extend(data["reviews"])
        if not data["has_next"] or len(reviews) >= limit:
            break
        payload["last_star_rating_id"] = reviews[-1]["id"]
    reviews = reviews[:limit]
    if group_by_buyer:
        merged_reviews: dict[str, list[dict[str, str]]] = {}
        for review in reviews:
            if review["username"] in merged_reviews:
                merged_reviews[review["username"]].append(review)
            else:
                merged_reviews[review["username"]] = [review]
        return merged_reviews
    session.close()
    return reviews
