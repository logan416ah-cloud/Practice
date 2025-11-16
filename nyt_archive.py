import requests
import pandas as pd
from getpass import getpass
from datetime import datetime
from tqdm import tqdm
from pathlib import Path


class NYTArchiveClient:
    def __init__(self, api_key):
        if not self.validate_key(api_key):
            raise ValueError("Invalid NYT API key.")
        self.api_key = api_key
        self.params = {"api-key": api_key}

    @staticmethod
    def validate_key(api_key):
        test_url = 'https://api.nytimes.com/svc/mostpopular/v2/emailed/7.json'
        response = requests.get(test_url, params={'api-key': api_key})
        if response.status_code == 200:
            return True
   
        print("\nERROR: Invalid NYT API Key.")
        try:
            print("Message", response.json().get("message"))
        except:
            pass

        return False

    @staticmethod
    def is_valid_year(year):
        try:
            year = int(year)
        except ValueError:
            return False
        return 1851 <= year <= datetime.today().year

    @staticmethod
    def is_valid_month(month):
        try:
            month = int(month)
        except ValueError:
            return False
        return 1 <= month <= 12

    def main_request(self, baseurl):
        try:
            response = requests.get(baseurl,params=self.params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Network/API error: {e}")
            return None

    def build_url(self):
        while True:
            try:
                year = int(input("What year would you like to retrieve? "))
                month = int(input("What month would you like to retrieve? (1-12) "))
            except ValueError:
                print("Please enter valid numbers for year and month.")
                continue

            if not self.is_valid_year(year):
                print("Enter a valid year between 1851 and the Current Year")
                continue
            
            if not self.is_valid_month(month):
                print("Please enter a valid month as an integer (1-12).")
                continue
        
            baseurl = f'https://api.nytimes.com/svc/archive/v1/{year}/{month}.json'
            print("URL:", baseurl)
            return baseurl, year, month

    @staticmethod
    def get_articles(data):
        article_list =[]

        for article in tqdm(data['response']['docs'], desc="Processing articles"):
            pub_date = article.get("pub_date")
            section_name = article.get("section_name")
            headline = article.get("headline", {}).get("main")
            web_url = article.get("web_url")

            article_dict ={
                'publish_date': pub_date,
                'section_name': section_name,
                'headline': headline,
                'url': web_url,
            }
            article_list.append(article_dict)

        article_df = pd.DataFrame(article_list)
        article_df['publish_date'] = (
            pd.to_datetime(article_df['publish_date'])
                .dt.strftime("%Y-%m-%d")
        )
        return article_df.sort_values(by='publish_date')

    def save_csv(self):
        baseurl, year, month = self.build_url()
        if not baseurl:
            return

        data = self.main_request(baseurl)
        if not data:
            return
        
        articles = self.get_articles(data)

        print("\nPREVIEW:")
        print(articles.head())

        choice = input("\nWould you like to save as CSV (y/n)? ").lower()
        if choice == 'y':
            folder = Path("NYT_Data")
            folder.mkdir(exist_ok=True)
            file_path = folder / f"nyt_{year}_{month}.csv"
            articles.to_csv(file_path, index=False)
    
            print(f"\nSaved as {file_path}")
            print(f"\nTotal articles retrieved: {len(articles)}")
        
    
    def choose_section(self, filename=None):
        if filename is None:
            year = int(input("What year would you like to retrieve? "))
            month = int(input("What month would you like to retrieve? (1-12) "))
            filename = f"nyt_{year}_{month}.csv"

        chosen_df = pd.read_csv(filename)

        section_choice = input("Which section would you like to sort by? ")
        
        filtered_df = chosen_df[chosen_df['section_name'] == section_choice]

        print(f"\nArticles in section '{section_choice}':")
        print(filtered_df.head())

        return filtered_df
