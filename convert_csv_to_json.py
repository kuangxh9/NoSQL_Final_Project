import os
import pandas as pd
import json
import re

input_dir = os.path.join(os.getcwd(), 'raw_data')
output_dir = os.path.join(os.getcwd(), 'converted_data')
os.makedirs(output_dir, exist_ok=True)

top_movie_input_file = os.path.join(input_dir, 'imdb (1000 movies) in june 2022.csv')
top_movie_output_file = os.path.join(output_dir, 'imdb_1000_movies.json')
top_movies_data = pd.read_csv(top_movie_input_file)
top_movies_data.columns = [col.strip() for col in top_movies_data.columns]

def process_top_movies(row):
    # Parse runtime
    runtime_raw = row.get("runtime", "")
    try:
        runtime = int(runtime_raw.replace("min", "").strip()) if "min" in runtime_raw else -1
    except ValueError:
        runtime = -1

    # Parse rating
    rating = row.get("RATING")
    try:
        rating = float(rating) if not pd.isna(rating) else -1
    except ValueError:
        rating = -1

    # Parse ranking
    ranking = row.get("ranking of movie", "").strip()
    if ranking == '1,000.00': ranking = '1000'

    # Parse year
    year_raw = row.get("Year", "")
    cleaned_year = re.sub(r"[^\d]", " ", year_raw).strip()
    year = cleaned_year.split()[0]

    # Parse certificate
    certificate = row.get("certificate", "")
    if not isinstance(certificate, str):
        certificate = ""

    # Parse metascore
    metascore_raw = row.get("metascore")
    try:
        metascore = int(metascore_raw) if not pd.isna(metascore_raw) else -1
    except ValueError:
        metascore = -1

    # Parse details
    details = row.get("DETAIL ABOUT MOVIE", "")
    if not isinstance(details, str):
        details = ""    
    
    # Parse actors
    actors = [
        row.get("ACTOR 1"),
        row.get("ACTOR 2"),
        row.get("ACTOR 3"),
        row.get("ACTOR 4")
    ]
    actors = [actor for actor in actors if isinstance(actor, str)]

    # Parse vote
    votes_raw = row.get("votes", "0")
    try:
        votes = int(str(votes_raw).replace(",", "").strip())
    except ValueError:
        votes = 0

    # Parse genre
    raw_genre = row.get("genre", "")
    if not isinstance(raw_genre, str):
        genre = []
    else:
        genre = raw_genre.split(', ')
        
    # Parse gross collection
    gross_raw = row.get("GROSS COLLECTION", "")
    try:
        gross_collection = float(gross_raw.replace("$", "").replace("M", "").strip())
    except:
        gross_collection = ""

    return {
        "ranking": int(ranking),
        "title": row.get("movie name", "").strip(),
        "year": int(year),
        "certificate": certificate,
        "runtime (min)": runtime,
        "genre": genre,
        "rating": rating,
        "metascore": metascore,
        "details": details,
        "director": row.get("DIRECTOR", "").strip(),
        "actors": actors,
        "votes": votes,
        "gross_collection (M)": gross_collection
    }


processed_top_movies_data = [process_top_movies(row) for _, row in top_movies_data.iterrows()]

with open(top_movie_output_file, 'w') as f:
    json.dump(processed_top_movies_data, f, indent=2)

print(f"JSON file created for top movies data.")