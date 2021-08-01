from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

headers = {
    "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "TE": "trailers"
}

payload = {
    "as_seller": "true",
    "last_score": "0",
    "page_size": "5"
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
    data_regex = r'(?<=perseusApp.initialData = ).+(?=;)'
    seller_url = f"https://www.fiverr.com/{username}"
    data = requests.get(seller_url, headers=headers)
    react_data = re.findall(data_regex, data.text)[0]
    seller_data = json.loads(react_data)
    return seller_data


@app.get("/")
def index():
    return {
        "Welcome to": "Unofficial Fiverr API",
        "For docs": "Visit /docs"}


@app.get("/{username}/reviews")
def get_reviews(username: str, filter_by: str = "positive",
                group_by_buyer: bool = True):
    URL = "https://www.fiverr.com/ratings/index"
    user_data = get_user_data(username)
    data = user_data["userData"]["buying_reviews"]
    reviews = data["reviews"]
    # Modifying headers
    reviews_headers["X-CSRF-Token"] = user_data["requestContext"]["csrf_token"]
    # Setting payload
    payload["user_id"] = user_data["userData"]["user"]["id"]
    payload["filter_by"] = filter_by
    while data["has_next"]:
        payload["last_star_rating_id"] = reviews[-1]["id"]
        data = requests.get(URL, headers=headers, data=payload)
        data = data.json()
        reviews.extend(data["reviews"])
    if not group_by_buyer:
        return reviews
    merged_reviews = {}
    for review in reviews:
        if review["username"] in merged_reviews.keys():
            merged_reviews[review["username"]].append(review)
        else:
            merged_reviews[review["username"]] = [review]
    return merged_reviews