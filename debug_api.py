import requests

url = "https://world.openfoodfacts.org/cgi/search.pl"
params = {
    "search_terms": "quinoa",
    "search_simple": 1,
    "action": "process",
    "json": 1,
    "page_size": 2,
    "fields": "product_name,nutriments,allergens_tags"
}
response = requests.get(url, params=params, timeout=5)
print(response.json())
