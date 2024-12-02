from pymongo import MongoClient
import json
import os

mongo_host = "root"
mongo_password = "password"
mongo_url = f"mongodb://{mongo_host}:{mongo_password}@final_proj:27017/"
client = MongoClient(mongo_url)

db_name = "mediaDatabase"
db = client[db_name]

# Drop database if it exists to remove old database
if db_name in client.list_database_names():
    client.drop_database(db_name)
    print(f"Existing database '{db_name}' deleted.")
print(f"Database '{db_name}' created.")

collections = {
    "topMovies": "imdb_1000_movies.json",
}

# Converted data directory
data_dir = "./converted_data" 

# Import JSON data into a collection
def import_json_to_collection(file_path, collection_name):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                db[collection_name].insert_many(data)
            elif isinstance(data, dict):
                db[collection_name].insert_one(data)
            print(f"Data from '{file_path}' imported into '{collection_name}'.")
    except Exception as e:
        print(f"Error importing '{file_path}' into '{collection_name}': {e}")

for collection_name, file_name in collections.items():
    file_path = os.path.join(data_dir, file_name)
    if os.path.exists(file_path):
        import_json_to_collection(file_path, collection_name)
    else:
        print(f"File '{file_path}' not found. Skipping '{collection_name}'.")

print("Imported collections:")
for collection in db.list_collection_names():
    print(f"- {collection}")
