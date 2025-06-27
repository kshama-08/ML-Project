import os
import requests
import streamlit as st
import pickle
import pandas as pd

# ------------------ Download Helper ------------------
def download_from_google_drive(file_id, destination):
    URL = "https://drive.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={'id': file_id}, stream=True)

    # Get confirmation token for large files
    token = None
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            token = value

    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)

    # Check if file is actually binary (not HTML)
    if 'text/html' in response.headers.get('Content-Type', ''):
        raise Exception("❌ Error: Google Drive returned an HTML page. Check permissions or file ID.")

    with open(destination, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)

# ------------------ Ensure similarity.pkl is downloaded ------------------
file_id = "1mwrApO6gckn-jOeOQsTo3J8QSd8PU0fv"
destination = "similarity.pkl"

if not os.path.exists(destination):
    st.info("📦 Downloading similarity.pkl from Google Drive...")
    download_from_google_drive(file_id, destination)
    st.success("✅ similarity.pkl downloaded successfully!")

# ------------------ Load Your Pickled Files ------------------
movies = pickle.load(open("movies.pkl", "rb"))
similarity = pickle.load(open("similarity.pkl", "rb"))



# TMDB API to get movie posters + movie info
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=4f6b62f9df6a3e7df1b729df5345c8d0&language=en-US"
    response = requests.get(url)
    if response.status_code != 200:
        return "https://via.placeholder.com/300x450?text=No+Image", "N/A", "N/A"

    data = response.json()
    poster_path = data.get('poster_path')
    rating = data.get('vote_average', 'N/A')
    release_date = data.get('release_date', 'N/A')

    if poster_path:
        full_poster_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    else:
        full_poster_path = "https://via.placeholder.com/300x450?text=No+Image"

    return full_poster_path, rating, release_date

# Recommend function
def recommend(movie):
    movie = movie.lower()
    if movie not in movies['title'].str.lower().values:
        return [], [], [], []

    idx = movies[movies['title'].str.lower() == movie].index[0]
    distances = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])

    recommended_movie_names = []
    recommended_movie_posters = []
    recommended_movie_ratings = []
    recommended_movie_years = []

    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        title = movies.iloc[i[0]].title
        poster, rating, release_date = fetch_movie_details(movie_id)

        recommended_movie_names.append(title)
        recommended_movie_posters.append(poster)
        recommended_movie_ratings.append(rating)
        recommended_movie_years.append(release_date[:4] if release_date != "N/A" else "N/A")

    return recommended_movie_names, recommended_movie_posters, recommended_movie_ratings, recommended_movie_years

# Streamlit UI
st.set_page_config(page_title="Movie Recommender System", page_icon="🎬", layout="wide")

st.title("🎬 Movie Recommender System")
st.markdown("Select a movie and get top 5 similar movie recommendations with posters, ratings, and release years!")


selected_movie_name = st.selectbox(
    "🎞️ Select a movie from the list",
    movies['title'].values
)

if st.button('Show Recommendations'):
    with st.spinner('Fetching Recommendations...🎥'):
        names, posters, ratings, years = recommend(selected_movie_name)

    if names:
        st.success("Here are some movies you might like:")

        cols = st.columns(5)  # display 5 movies in a row
        for idx, col in enumerate(cols):
            with col:
                st.image(posters[idx], width=150)
                st.markdown(f"**{names[idx]}**")
                st.markdown(f"⭐ Rating: {ratings[idx]}")
                st.markdown(f"📅 Year: {years[idx]}")
    else:
        st.error("Movie not found or no recommendations available! Please try another movie.")

