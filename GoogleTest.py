# from serpapi import GoogleSearch
import requests
import pprint
import pandas as pd


url = 'https://serpapi.com/search.json'

job_title = input("Enter job ")
location = input("Enter state ")

q = job_title + '' + location

params = {
    "engine": "google_jobs",
    "q": q,
    "hl": "en",
    "api_key": ""
    }

search = requests.get(url, params=params)
results = search.json()
job_list = []

for job in results.get("jobs_results", []):
    job_dict = {
        'job_title': job.get("title"),
        'company': job.get("company_name"),
        'location': job.get("location"),
        'description': job.get("description"),
        'link': job.get("link")
    }
    job_list.append(job_dict)

job_df = pd.DataFrame(job_list)

# results = pd.DataFrame(results)
# jobs_results = results

# pprint.pprint(jobs_results)

print(job_df)
