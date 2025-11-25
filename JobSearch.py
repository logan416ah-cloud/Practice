import requests
from pathlib import Path
import pandas as pd
import datetime as dt
from tqdm import tqdm


class JobSearch:
    """
    Searches for job listings using SerpApi's Google Jobs API.

    Attributes:
        api_key (str): SerpApi API Key.
    """

    def __init__(self, api_key):
        """
        Initializes the client with the url and validates the API Key.

        Args:
            api_key (str): Your SerpApi API Key
        
        Raises:
            ValueError: If the API key is invalid. 
        """

        self.url = 'https://serpapi.com/search.json'
        self.api_key = api_key

        if not self.validate_key(api_key):
            raise ValueError("Invalid key")

    @staticmethod
    def validate_key(api_key):
        """
        Validates your API key by using a test request.

        Args:
            api_key (str): SerpApi API Key to validate

        Returns:
            bool: True if key is valid, False if not. 
        """

        url = 'https://serpapi.com/search.json'
        params = {
            "engine": "google_jobs",
            "q": "test",
            "hl": "en",
            "api_key": api_key,
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return True
            else:
                print(f"WARNING: API KEY may be invalid. Status code: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"WARNING: API KEY check failed. Error: {e}")
        return False

    def search(self, job_title, location, save=False):
        """
        Searches for job listings within any specified state in the United States.

        Args:
            job_title (str): Career/Job title you want to search.
            location (str): The state you want your job search to take place.
            save (bool): Whether you want to save results to your computer.
        
        Returns:
            pd.DataFrame: DataFrame of all search results.
        """
        job_list = []
        next_page_token = None
        q = f"{job_title} {location}"

        page_count = 0

        with tqdm(desc="Fetching pages", unit='pages') as pbar:
            while True:
                params = {
                    "engine": "google_jobs",
                    "q": q,
                    "hl": "en",
                    "api_key": self.api_key,
                }

                if next_page_token:
                    params['next_page_token'] = next_page_token

                search = requests.get(self.url, params=params)
                results = search.json()

                jobs = results.get("jobs_results", [])

                if not jobs:
                    break

                for job in jobs:
                    job_list.append({
                        'job_title': job.get("title"),
                        'company': job.get("company_name"),
                        'location': job.get("location"),
                        'Qualifications': job.get('job_highlights', [{}])[0].get("items", []),
                        'salary': job.get('detected_extensions', {}).get('salary'),
                        'description': job.get("description"),
                        'link': job.get("share_link")
                    })

                next_page_token = results.get("serpapi_pagination", {}).get("next_page_token")

                pbar.update(1)

                if not next_page_token:
                    break

            job_df = pd.DataFrame(job_list)

            if save:
                current_date = dt.datetime.today()

                today = current_date.strftime("%Y-%m-%d")
                folder = Path("Job_Listings")
                folder.mkdir(exist_ok=True)

                safe_title = job_title.replace(" ", "_")
                file_path = folder / f"{location}_{safe_title}_jobs_{today}.csv"
                job_df.to_csv(file_path, index=False)
            else:
                return job_df

    def search_all_states(self, job_title, save=False):
        states = [
            "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
            "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
            "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
            "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
            "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
            "New Hampshire", "New Jersey", "New Mexico", "New York",
            "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
            "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
            "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
            "West Virginia", "Wisconsin", "Wyoming"
        ]

        current_date = dt.datetime.today()
        today = current_date.strftime("%Y-%m-%d")
        folder = Path("Job_Listings")
        folder.mkdir(exist_ok=True)

        safe_title = job_title.replace(" ", "_")


        all_jobs = []

        for state in tqdm(states, desc="Searching through states...", unit='state'):
            print(f"Searching {state}...")

            state_df = self.search(job_title, state, save=False)

            if state_df is not None and not state_df.empty:
                state_df["state"] = state
                all_jobs.append(state_df)

                if save:
                    state_file_path = folder / f"{state}_{safe_title}_jobs_{today}.csv"
                    state_df.to_csv(state_file_path, index=False)
        
        combined_jobs = pd.concat(all_jobs, ignore_index=True) if all_jobs else pd.DataFrame()

        if save:
            combined_path = folder / f"ALL_STATE_{safe_title}_jobs_{today}.csv"
            combined_jobs.to_csv(combined_path, index=False)

        return combined_jobs


class Clean:
    def __init__(self):

        self.base_path = Path(__file__).parent
        self.data_folder = self.base_path / "Job_Listings"
        if not self.data_folder.exists():
            print("No Jobs_Listing folder. Run JobSearch.search()")
            
    def create_dataset(
            self, 
            job_title, 
            location=None, 
            all_states=False, 
            save=False,
            year=None,
            month=None,
            day=None,
            date=None,
            ):
        
        job_title_safe = job_title.replace(" ","_")
        valid = (all_states and location is None) or (not all_states and location is not None)

        if not valid:
            raise ValueError("You must specify a location OR set ALL=True")

        if save and not all_states:
            raise ValueError("Dataset already saved to computer")

        if location is not None:
            location_safe = location.replace(" ","_")
            prefix = f"{location_safe}_{job_title_safe}_jobs_"
        else:
            prefix = f"*_{job_title_safe}_jobs_"

        if date:
            year = date.year
            month = date.month
            day = date.day

        if date or year or month or day:

            if (month or day) and not year:
                raise ValueError("Year is required when filtering by month or day.")

            if year and month and day:
                file_pattern = f"{prefix}{year}-{month:02d}-{day:02d}.csv"
            elif year and month:
                file_pattern = f"{prefix}{year}-{month:02d}-*.csv"
            elif year:
                file_pattern = f"{prefix}{year}-*.csv"

        else:
            file_pattern = f"{prefix}*.csv"

        files = list(self.data_folder.glob(file_pattern))

        if not files:
            print("No data files found.")
            return pd.DataFrame()
        
        datasets = []

        for f in tqdm(files, desc="Loading job data", unit='file'):
            try:
                df = pd.read_csv(f)
            except pd.errors.EmptyDataError:
                print(f"\nEmpty CSV skipped: {f}")
                continue
            
            datasets.append(df)
        
        combined_df = pd.concat(datasets, ignore_index=True) if datasets else pd.DataFrame()

        if save and all_states:
            save_path = self.base_path / "Job_Listings" / "Custom_dataset_folder"
            save_path.mkdir(exist_ok=True)

            file_path = save_path / f"combined_{job_title_safe}_dataset.csv"
            combined_df.to_csv(file_path, index=False)

        print(f"Combined dataset created with {len(combined_df)} rows.")
        return combined_df


# if __name__=='__main__':

#     j = JobSearch('Your_API_Key')

#     my_search = j.search_all_states('Cybersecurity', save=True)
#     print(my_search)
