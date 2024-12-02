from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
from collections import Counter
import os
import json

app = Flask(__name__)

app.secret_key = os.urandom(24)

# Connect to MongoDB on local host (path - 27017:27017) in Docker container
# To run the app locally, use http://localhost:5000/
mongo_host = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "password")
mongo_url = f"mongodb://root:{mongo_password}@final_proj:27017/"
client = MongoClient(mongo_url)

db_name = "mediaDatabase"
db = client[db_name]

movies_collection = db["topMovies"]

@app.route("/")
def home():
    """Welcome message."""
    return render_template("index.html")

# Movies overview Page
@app.route("/movies_overview", methods=["GET"])
def movies_overview():

    title = request.args.get("title", "").strip()
    year_min = request.args.get("year_min", None, type=int)
    year_max = request.args.get("year_max", None, type=int)
    rating_min = request.args.get("rating_min", None, type=float)
    rating_max = request.args.get("rating_max", None, type=float)
    genre = request.args.getlist("genre") 
    sort_by = request.args.get("sort_by", "").strip()

    query = {}
    if title:
        query["title"] = title
    if year_min is not None or year_max is not None:
        query["year"] = {}
        if year_min is not None:
            query["year"]["$gte"] = year_min
        if year_max is not None:
            query["year"]["$lte"] = year_max
    if rating_min is not None or rating_max is not None:
        query["rating"] = {}
        if rating_min is not None:
            query["rating"]["$gte"] = rating_min
        if rating_max is not None:
            query["rating"]["$lte"] = rating_max
    if genre:
        query["genre"] = {"$all": genre}

    sort = [("title", 1)]
    if sort_by == "rating":
        sort = [("rating", -1)]
    elif sort_by == "metascore":
        sort = [("metascore", -1)]
    elif sort_by == "year":
        sort = [("year", -1)]
    elif sort_by == "votes":
        sort = [("votes", -1)]

    # Fetch all movies from MongoDB
    movies = list(movies_collection.find(query, {"_id": 0}).sort(sort))
    total_count = len(movies)

    return render_template("movies_overview.html", movies=movies, total_count=total_count)

# Movies cast Page
@app.route("/movies_cast", methods=["GET"])
def movies_cast():
    action = request.args.get("action", "apply_filters")
    name = request.args.get("name", "").strip()
    role = request.args.get("role", "").strip()
    sort_by = request.args.get("sort_by", "year")

    if action == "apply_filters":
        query = {}
        if role == "director":
            query["director"] = name
        elif role == "actor":
            query["actors"] = name
        movies = list(
            movies_collection.find(query, {"_id": 0}).sort(sort_by, -1)
        )
        return render_template("movies_cast.html", action="apply_filters", movies=movies)

    elif action == "show_stats":
        pipeline = [
            {"$group": {
                "_id": "$director",
                "movies_count": {"$sum": 1},
                "avg_rating": {"$avg": "$rating"},
                "avg_metascore": {"$avg": "$metascore"},
                "avg_gross": {"$avg": "$gross_collection (M)"},
            }},
            {"$sort": {"movies_count": -1}},
        ]
        directors = list(movies_collection.aggregate(pipeline))
        return render_template("movies_cast.html", action="show_stats", directors=directors)

@app.route("/movies_update", methods=["GET", "POST"])
def movies_update():
    if request.method == "GET":
        title = request.args.get("title", "").strip()
        movie = None
        if title:
            movie = movies_collection.find_one({"title": title}, {"_id": 0})
            if not movie:
                flash(f"No movie found with title '{title}'.", "warning")
        return render_template("movies_update.html", title=title, movie=movie)

    elif request.method == "POST":
        original_title = request.form.get("original_title")
        updated_data = {
            "title": request.form.get("title").strip(),
            "year": int(request.form.get("year")) if request.form.get("year") else None,
            "certificate": request.form.get("certificate").strip(),
            "runtime (min)": int(request.form.get("runtime")) if request.form.get("runtime") else None,
            "rating": float(request.form.get("rating")) if request.form.get("rating") else None,
            "metascore": int(request.form.get("metascore")) if request.form.get("metascore") else None,
            "details": request.form.get("details").strip(),
            "director": request.form.get("director").strip(),
            "actors": [actor.strip() for actor in request.form.get("actors", "").split(",") if actor.strip()],
            "genre": [genre.strip() for genre in request.form.get("genre", "").split(",") if genre.strip()],
            "votes": int(request.form.get("votes")) if request.form.get("votes") else None,
            "gross_collection (M)": float(request.form.get("gross_collection")) if request.form.get("gross_collection") else None
        }

        updated_data = {k: v for k, v in updated_data.items() if v is not None}
        result = movies_collection.update_one({"title": original_title}, {"$set": updated_data})

        if result.matched_count:
            flash(f"Movie '{original_title}' updated successfully!", "success")
        else:
            flash(f"Failed to update movie '{original_title}'.", "danger")

        return redirect(url_for("movies_update"))

@app.route("/movies_insert", methods=["GET", "POST"])
def movies_insert():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        year = request.form.get("year", "").strip()
        certificate = request.form.get("certificate", "").strip()
        runtime = request.form.get("runtime", "").strip()
        rating = request.form.get("rating", "").strip()
        metascore = request.form.get("metascore", "").strip()
        genre = request.form.get("genre", "").strip().split(",")
        votes = request.form.get("votes", "").strip()
        gross_collection = request.form.get("gross_collection", "").strip()
        director = request.form.get("director", "").strip()
        actors = request.form.get("actors", "").strip().split(",")
        details = request.form.get("details", "").strip()

        if not title or not year or not genre:
            flash("Title, Year, and Genre are required fields.", "danger")
            return redirect("/movies_insert")

        new_movie = {
            "title": title,
            "year": int(year) if year.isdigit() else None,
            "certificate": certificate,
            "runtime (min)": int(runtime) if runtime.isdigit() else None,
            "rating": float(rating) if rating.replace(".", "").isdigit() else None,
            "metascore": int(metascore) if metascore.isdigit() else None,
            "genre": [g.strip() for g in genre if g.strip()],
            "votes": int(votes) if votes.isdigit() else None,
            "gross_collection (M)": float(gross_collection) if gross_collection.replace(".", "").isdigit() else None,
            "director": director,
            "actors": [a.strip() for a in actors if a.strip()],
            "details": details,
        }

        try:
            movies_collection.insert_one(new_movie)
            flash(f"Movie '{title}' was successfully added to the database.", "success")
        except Exception as e:
            flash(f"An error occurred while adding the movie: {str(e)}", "danger")

        return redirect("/movies_insert")

    return render_template("movies_insert.html")

@app.route("/movies_delete", methods=["GET", "POST"])
def movies_delete():
    if request.method == "POST":
        # Get the title from the form
        title = request.form.get("title", "").strip()

        if not title:
            flash("Please provide a movie title.", "danger")
            return redirect("/movies_delete")

        # Search for the movie in the database
        result = movies_collection.delete_one({"title": title})

        if result.deleted_count > 0:
            # Movie was successfully deleted
            flash(f"Movie '{title}' has been successfully deleted.", "success")
        else:
            # No matching movie was found
            flash(f"No movie found with title '{title}'.", "warning")

        return redirect("/movies_delete")

    # Render the delete page for GET requests
    return render_template("movies_delete.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)