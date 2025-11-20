import requests
import pandas as pd
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

            try:
                return response.json()
            except ValueError:
                print("Error: Response is not a valid JSON")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Network/API error: {e}")
            return None

    def build_url(self, year=None, month=None):

        # If not provided -> ask user
        if year is None or month is None:
            while True:
                try:
                    year = int(input("Enter year: "))
                    month = int(input("Enter month (1-12): "))
                except ValueError:
                    print("Enter valid integers.")
                    continue
                
                if self.is_valid_year(year) and self.is_valid_month(month):
                    break

                print("Invalid date. Try again.")

        # Validate programmatic input
        if not self.is_valid_year(year):
            raise ValueError("Invalid year")
        if not self.is_valid_month(month):
            raise ValueError("Invalid month")
        
        baseurl = f'https://api.nytimes.com/svc/archive/v1/{year}/{month}.json'
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

    def save_csv(self, year=None, month=None):

        if year is None or month is None:
            baseurl, year, month = self.build_url()
        else:
            baseurl = f"https://api.nytimes.com/svc/archive/v1/{year}/{month}.json"

        data = self.main_request(baseurl)
        if not data:
            return
        
        articles = self.get_articles(data)

        folder = Path("NYT_Data")
        folder.mkdir(exist_ok=True)
        file_path = folder / f"nyt_{year}_{month}.csv"
        articles.to_csv(file_path, index=False)

        return(f"\nSaved as {file_path}. Total articles retrieved: {len(articles)}")
    
class Pullexistingdata:
    def __init__(self):
        self.start_year = 1851
        self.end_year = datetime.today().year
        self.file_list =[]
        self._combined = None # cache for combined DataFrame

    def fetch_files(self):
        for file in Path("NYT_Data").glob("nyt_*.csv"):
            self.file_list.append(file)
                                  
        self.file_df = pd.DataFrame(self.file_list)
        return self.file_df

    def read_csv_files(self):
        if not self.file_list:
            self.fetch_files()
        
        dataframes = []
        for file in self.file_list:
            df = pd.read_csv(file)
            dataframes.append(df)

        return dataframes
    
    def combine_all(self):
        # If already cached, return cahced version
        if self._combined is not None:
            return self._combined

        dfs = self.read_csv_files()
        if not dfs:
            return pd.DataFrame()
        
        self._combined = pd.concat(dfs, ignore_index=True)
        return self._combined
    
    def filter_by_date(self, year: int, month: int, day: int) -> pd.DataFrame:
        """
        Filters the combined dataframe by a date from
        publish_date. Returns a DataFrame.
        """
        df = self.combine_all()
        if df.empty:
            return pd.DataFrame()

        df['publish_date'] = pd.to_datetime(df['publish_date'])

        target_date = pd.Timestamp(year=int(year), month=int(month), day=int(day))
        
        result = df[df['publish_date'].dt.date == target_date.date()]

        return result

    def filter_by_section(self, section):
        """
        Filters the combined dataframe by a partial (case-insensitive)
        match on section_name. Returns a DataFrame.
        """
        df = self.combine_all()
        if df.empty:
            return pd.DataFrame()
        
        result = df[df['section_name'].str.contains(section, case=False, na=False)]
        return result
    
    def filter_by_headline(self, *keywords):
        """
        Filters the combined dataframe by specifed keywords (case-insensitive)
        from the available headlines. Returns a DataFrame.
        """
        df = self.combine_all()
        if df.empty or not keywords:
            return pd.DataFrame()
        
        keywords = "|".join(keywords)
        result = df[df['headline'].str.contains(keywords, case=False, na=False)]
        return result
    
    def show_available(self):
        df = self.combine_all()
        if df.empty:
            return pd.DataFrame()
        
        df['publish_date'] = pd.to_datetime(df['publish_date'], errors='coerce')

        available_dates = df['publish_date'].dt.to_period('M').unique()
        available_sections = df['section_name'].dropna().unique()

        print("Available dates:")
        for d in sorted(available_dates):
            print(" -", d)

        print("Available sections:")
        for s in sorted(available_sections):
            print(" -", s)
