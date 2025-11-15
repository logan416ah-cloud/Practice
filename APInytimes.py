import requests
import pandas as pd
from datetime import datetime
from getpass import getpass
from pathlib import Path

baseurl = 'https://api.nytimes.com/svc/mostpopular/v2/viewed/7.json'

def validate_key(api_key):
    test_url = 'https://api.nytimes.com/svc/mostpopular/v2/viewed/7.json'
    response = requests.get(test_url, params={'api-key': api_key})

   
    if response.status_code == 200:
        return True
   
    print("\nERROR: Invalid NYT API Key.")
    try:
        print("Message", response.json().get("message"))
    except:
        pass

    return False

while True:
    API_KEY = getpass("Enter your NYT API Key: ")
    if validate_key(API_KEY):
        break
    print("Invalid key, please try again.")


params = {'api-key':API_KEY}

def main_request(baseurl):
    try:
        response = requests.get(baseurl,params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Network/API error: {e}")
        exit()

def parse_json(response):
    article_list = []
    for item in response['results']:
        article ={
            'id': item['id'],
            'pd': item['published_date'],
            'title': item['title'],
            'url': item['url'],
        }
        article_list.append(article)
    article_df = pd.DataFrame(article_list)
    return article_df

response_data = main_request(baseurl)

try:
    data = parse_json(response_data)
    if data.empty:
        print("No articles returned.")
        exit()
except KeyError as e: # Catch JSON structure issues
    print(f"Unexpected JSON format, missing key: {e}")
    exit()

print(data)

choice = input("\nWould you like to save as CSV (y/n)? ").lower()

if choice == 'y':
    folder = Path("NYT_Data")
    folder.mkdir(exist_ok=True)

    todays_date = datetime.now().strftime("%Y-%m-%d")
    filename = input("\nSave file as? ")
    file_path = folder / f"{filename}_{todays_date}.csv"

    data.to_csv(file_path, index=False)
    print(f"Saved as {file_path}")
else:
    print("Closing program.")
