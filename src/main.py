"""
Unofficial Fiverr API helps you to get:

* Seller Details
* Seller Gigs
* Seller Orders
* Seller Transactions
* Seller Reviews
    * Group by buyers
    * Filter by Impression
    * Sort by time
    * Limit no. of reviews
"""

from typing import Union
from enum import Enum
import json
from cloudscraper.exceptions import CloudflareChallengeError

from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi import Depends, FastAPI, HTTPException, status
from bs4 import BeautifulSoup
import requests
import cloudscraper

DESCRIPTION = __doc__ or ""
tags_metadata = [
    {"name": "Home"},
    {"name": "Seller Details", "description": "Get details about seller"},
]

URL = "https://www.fiverr.com"
bearer_description = f"""
### Steps to obtain authorization token from Fiverr:
- Login into your [Fiverr account]({URL})
- Open Network Tab of browser
- Select any `HTML` or `XHR` request
- Go to `Cookies` tab
- Use `hodor_creds` as authorization token

> I DO NOT store your credentials. You can verify that by viewing source code [here](https://www.github.com/salmannotkhan/fiverr-api)
"""

bearer = HTTPBearer(auto_error=True, description=bearer_description)

app = FastAPI(
    title="Unofficial Fiverr API",
    description=DESCRIPTION,
    version="1.2",
    contact={
        "name": "Salman Shaikh",
        "url": "https://salmannotkhan.github.io/",
        "email": "tony903212@gmail.com",
    },
    openapi_tags=tags_metadata,
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


common_headers = {
    "User-Agent": "Mozilla Firefox",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Requested-With": "XMLHttpRequest",
}

def get_user_data(username: str):
    """
    Get basic seller details and CSRF Token
    """
    scraper = cloudscraper.create_scraper()
    seller_url = f"{URL}/{username}"
    data = scraper.get(seller_url)
    soup = BeautifulSoup(data.text, "lxml")
    seller_data = json.loads(
        soup.find("script", id="perseus-initial-props").string or "null"
    )
    seller_data["csrfToken"] = soup.find("meta", {"property": "csrfToken"}).get(
        "content"
    )
    return scraper.cookies, seller_data


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


@app.get("/transaction", tags=["Seller Details"])
async def get_transactions(after: Union[str, None] = None, token=Depends(bearer)):
    """
    Use `endCursor` as `after` for pagination
    """
    scraper = cloudscraper.create_scraper()
    url = f"{URL}/perseus/financial-dashboard/api/earnings/transactions"
    cookies = {"hodor_creds": token.credentials}
    while True:
        try:
            res = scraper.get(
                url,
                headers=common_headers,
                cookies=cookies,
                allow_redirects=False,
                params={"after": after},
            )
            break
        except CloudflareChallengeError:
            pass
    data = res.json()
    data["data"]["transactions"] = list(
        map(
            lambda x: {**x, "amount": (x["amount"] / 100)}, data["data"]["transactions"]
        )
    )
    return data


@app.get("/{username}", tags=["Seller Details"])
async def get_seller_details(username: str):
    """
    Remove unnecessary details from seller card and returns it
    """
    _, user_data = get_user_data(username)
    seller_card = user_data["userData"]["seller_card"]
    seller_profile = user_data["userData"]["seller_profile"]
    seller_card.update(seller_profile)
    return seller_card


@app.get("/{username}/gigs", tags=["Seller Details"])
async def get_gigs(username: str):
    """
    Get seller gigs
    """
    _, user_data = get_user_data(username)
    return user_data["gigs"]["gigs"]


@app.get("/{username}/reviews", tags=["Seller Details"])
async def get_reviews(
    username: str,
    filter_by: Union[FilterBy, None] = None,
    sort_by: Union[SortBy, None] = None,
    group_by_buyer: bool = False,
    limit: int = 9999,
):
    """
    Get seller reviews
    """
    session = requests.session()
    cookies, user_data = get_user_data(username)
    session.cookies = cookies
    url = f"{URL}/reviews/user_page/fetch_user_reviews/{user_data['userData']['user']['id']}"

    # Adding CSRF Token
    common_headers["X-CSRF-Token"] = user_data["csrfToken"]
    common_headers["Referer"] = f"https://www.fiverr.com/{username}"
    # Setting up payload
    payload: dict[str, str] = {}
    payload["user_id"] = user_data["userData"]["user"]["id"]
    if filter_by:
        payload["filter_by"] = filter_by.value
    if sort_by:
        payload["sort_by"] = sort_by.value
    reviews: list[dict[str, str]] = []

    scraper = cloudscraper.create_scraper(sess=session, browser="chrome")
    while True:
        data = scraper.get(url, headers=common_headers, params=payload)
        data = data.json()
        reviews.extend(data["reviews"])
        if not data["has_next"] or len(reviews) >= limit:
            break
        payload["last_star_rating_id"] = reviews[-1]["id"]
        payload["last_review_id"] = reviews[-1]["id"]
        payload["last_score"] = "0"
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


@app.get("/{username}/orders", tags=["Seller Details"])
async def get_orders(username: str, token=Depends(bearer)):
    url = f"{URL}/users/{username}/manage_orders/type/completed"
    cookies = {"hodor_creds": token.credentials}
    results = []
    scraper = cloudscraper.create_scraper()
    while True:
        while True:
            try:
                res = scraper.get(
                    url, headers=common_headers, cookies=cookies, allow_redirects=False
                )
                break
            except CloudflareChallengeError:
                pass

        if res.status_code == 302:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized profile"
            )
        data = res.json()
        results.extend(data["results"])
        if not data.get("load_more_url"):
            break
        url = "https://www.fiverr.com" + data["load_more_url"]
    return results
