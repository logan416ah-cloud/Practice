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

if __name__=='__main__':

    j = JobSearch('Your_API_Key')

    my_search = j.search_all_states('Cybersecurity', save=True)
    print(my_search)
