# This program pulls archived articles from the New York Times API.
# It requires a valid NYT API Key and a range of years to download.
# 
# Note: The NYT API allows a maximum of 5 requests per minute, so 
#       the program waits 12 seconds between requests.
#
# EXAMPLE USE FOR NYTArchiveClient:
#
# my_key = 'your NYT API key'
# client = NYTArchiveClient('my_key', 1996, 1999)
# client.start_download()
# 
# This will download articles for every month between 1996 and 1999.
# 
# IMPORTANT: You must have a valid NYT API Key for this to work.
#
# -------------------------------------------
# EXAMPLE USE FOR Tickler():
# 
# tickle = Tickler()
# print(tickle.filter_by_headline('Trump'))
# 
# EXAMPLE OUTPUT:
# 
#         publish_date  section_name        headline              url
# 6         2023-11-14          U.S.    Blah Blah Blah...   https://www.nytimes.com/
# 29        2021-01-01       Climate    Blah Blah Blah...   https://www.nytimes.com/
# 79        2020-04-01      New York    Blah Blah Blah...   https://www.nytimes.com/
# 88        2017-09-04       Opinion    Blah Blah Blah...   https://www.nytimes.com/
# 91        2009-07-19          U.S.    Blah Blah Blah...   https://www.nytimes.com/
#
# [472 rows x 4 columns]



import requests
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from pathlib import Path
import time

class NYTArchiveClient():
    """
    A client for downloading New York Times articles from the archive API.

    Attributes:
        years (range): Range of years to download.
        months (range): Range of months (1-12) to download.
        api_key (str): NYT API key.
    """

    def __init__(self, api_key, year1, year2):
        """
        Initializes the client with a year range and validates the API key.

        Args:
            api_key(str): Your NYT API key.
            year1 (int): Starting year for archive download
            year2 (int): Ending year for archive download

        Raises:
            ValueError: If the API key is invalid, years are not integers.
                        year1 > year2, or years are not in range.
        """

        if not self.validate_key(api_key):
            raise ValueError("Invalid NYT API key")
        try:
            year1 = int(year1)
            year2 = int(year2)
        except ValueError:
            raise ValueError("year1 and year2 must be integers")

        if year1 > year2:
            raise ValueError("year1 must be less than or equal to year2")
        if not self.is_valid_year(year1) or not self.is_valid_year(year2):
            raise ValueError(
                "NYT archive starts at 1851"
                "Please enter a year range that starts after 1851" 
            )
        
        self.years = range(year1, year2 + 1)
        self.months = range(1, 13)
        self.api_key = api_key
        self.params = {"api-key": api_key}
    
    @staticmethod
    def validate_key(api_key): 
        """
        Validates your API key by using a test request.

        Args:
            api_key (str): NYT API key to validate

        Returns:
            bool: True if key is valid, False if not.
        """

        test_url = 'https://api.nytimes.com/svc/mostpopular/v2/emailed/7.json'
        try:
            response = requests.get(test_url, params={'api-key': api_key}, timeout=7)
            if response.status_code == 200:
                return True
            else:
                print(f"WARNING: API KEY may be invalid. Status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"WARNING: API KEY check failed. Error: {e}")
        return False

    @staticmethod
    def is_valid_year(year):
        """
        Validates whether if a year falls within the valid NYT archive range.

        Args:
            year (int):Year to check.

        Returns:
            bool: True if year is between 1851 and the current year. False if not.
        """
        try:
            year = int(year)
        except ValueError:
            return False
        return 1851 <= year <= datetime.today().year

    def start_download(self):
        """
        Downloads NYT articles for the specified year/month range
        and saves each month as a CSV file in 'NYT_Data' folder.
        """

        folder = Path("NYT_Data")
        folder.mkdir(exist_ok=True)

        # Loop through the years and months, download data
        for year in tqdm(self.years, desc='Years'):
            for month in tqdm(self.months, desc=f"Year {year}", leave=False):

                baseurl = f'https://api.nytimes.com/svc/archive/v1/{year}/{month}.json'
                response = requests.get(baseurl, params=self.params)

                try:
                    data = response.json()
                except ValueError:
                    print(f"Error: Invalid JSON for: {year} and {month}")
                    continue

                docs = data.get("response", {}).get("docs", [])
                article_list = []

                # Extract relevant article information
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

                # Convert to DataFrame
                article_df = pd.DataFrame(article_list)

                if not article_df.empty:
                    # Standardize data format
                    article_df['publish_date'] =(
                        pd.to_datetime(article_df['publish_date'])
                            .dt.strftime("%Y-%m-%d")
                    )

                # Save CSV for each month
                file_path = folder / f"nyt_{year}_{month}.csv"
                article_df.to_csv(file_path, index=False)

                time.sleep(12) # IMPORTANT - NYT API allows for 5 requests a minute.

class Tickler:
    """
    Handles combining and filtering downloaded NYT archive CSVs.

    Attributes:
        start_year (int): Earliest NYT archive year.
        end_year (int): Current year.
        _combined (DataFrame): Cached combined DataFrame of all CSVs.
        _snapshot (dict): Tracks file modification times for caching
    """

    def __init__(self):
        self.start_year = 1851
        self.end_year = datetime.today().year

        self._combined = None
        self._snapshot = {}

        data_folder = Path("NYT_Data")
        if not data_folder.exists():
            print(
                "NYT_Data folder missing\n"
                "Creating folder now\n" 
                "Be sure to run NYTArchiveClient.start_download() to download archives"
                )
            data_folder.mkdir()
            
    def combine_all(self, year1=None, year2=None):
        """
        Combines all CSV files into a single DataFrame.
        Uses caching to avoid reloading unchanged files.

        Args:
            year1 (int, optional): Start year to filter files.
            year2 (int, optional): End year to filter files.

        Returns:
            pd.DataFrame: Combined DataFrame of all CSV articles.
        """

        if year1 is not None and year2 is not None:
            search_path = Path(f"NYT_Data/{year1}-{year2}")
        else:
            search_path = Path("NYT_Data")

        files = list(search_path.rglob("nyt_*.csv"))
        current_snapshot = {f: f.stat().st_mtime for f in files}

        if self._combined is not None and current_snapshot == self._snapshot:
            return self._combined

        mainframe= []
        for f in files:
            df = pd.read_csv(f)
            df['publish_date'] = pd.to_datetime(df["publish_date"])
            mainframe.append(df)

        self._combined = pd.concat(mainframe, ignore_index=True) if mainframe else pd.DataFrame()
        self._snapshot = current_snapshot

        return self._combined
    
    def filter_by_date(self, year: int, month: int, day: int) -> pd.DataFrame:
        """
        Filters the combined dataframe by a specific date.

        Args:
            year (int)
            month (int)
            day (int)
        
        Returns:
            pd.DataFrame: Filtered DataFrame with articles published on the specified date.
        """

        df = self.combine_all()
        if df.empty:
            return pd.DataFrame()

        # df['publish_date'] = pd.to_datetime(df['publish_date'])

        target_date = pd.Timestamp(year=int(year), month=int(month), day=int(day))
        
        result = df[df['publish_date'].dt.date == target_date.date()]

        return result

    def filter_by_section(self, section):
        """
        Filters the combined dataframe by section name (case-insensitive)

        Args:
            section (str)

        Returns:
            pd.DataFrame: Filtered DataFrame.
        """

        df = self.combine_all()
        if df.empty:
            return pd.DataFrame()
        
        result = df[df['section_name'].str.contains(section, case=False, na=False)]
        return result
    
    def filter_by_headline(self, *keywords):
        """
        Filters the combined dataframe by headline keywords (case-insensitive)

        Args:
            *keywords: One or more keywords.

        Returns:
            pd.DataFrame: Filtered DataFrame
        """

        df = self.combine_all()
        if df.empty or not keywords:
            return pd.DataFrame()
        
        keywords = "|".join(keywords)
        result = df[df['headline'].str.contains(keywords, case=False, na=False)]
        return result
    
    def show_available(self):
        """
        Prints available months and sections in the combined dataset.
        """

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
        for s in sorted(available_sections, key=str.lower):
            print(" -", s)
