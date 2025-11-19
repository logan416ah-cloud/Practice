import requests
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from pathlib import Path
import time

class NYTArchiveClient():
    def __init__(self, api_key):
        self.years = range(1996, 2026)
        self.months = range(1, 13)
        self.api_key = api_key
        self.params = {"api-key": api_key}

    def start_download(self):
        folder = Path("NYT_Data")
        folder.mkdir(exist_ok=True)

        for year in tqdm(self.years, desc='Years'):
            for month in tqdm(self.months, desc=f"Year {year}", leave=False):

                baseurl = f'https://api.nytimes.com/svc/archive/v1/{year}/{month}.json'
                response = requests.get(baseurl, params=self.params)

                try:
                    data = response.json()
                except ValueError:
                    print(f"Error: Invalid JSON for: {year} and {month}")

                docs = data.get("response", {}).get("docs", [])
                article_list = []

                for article in docs:
                    pub_date = article.get("pub_date")
                    section_name = article.get("section_name")
                    headline = article.get("headline", {}).get("main")
                    web_url = article.get("web_url")

                    article_dict = {
                        'publish_date': pub_date,
                        'section_name': section_name,
                        'headline': headline,
                        'url': web_url,
                    }
                    article_list.append(article_dict)

                article_df = pd.DataFrame(article_list)

                if not article_df.empty:
                    article_df['publish_date'] =(
                        pd.to_datetime(article_df['publish_date'])
                            .dt.strftime("%Y-%m-%d")
                    )

               
                file_path = folder / f"nyt_{year}_{month}.csv"
                article_df.to_csv(file_path, index=False)

                time.sleep(1)
