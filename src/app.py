from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import csv
import io

app = Flask(__name__, template_folder='.', static_folder='.')
CORS(app)  # Enable CORS for frontend requests

# ==================== IN-MEMORY STORAGE ====================
# Store clicked movies for future Google Gemini API integration
clicked_movies = []

# Sample movie data (will be replaced by API data later)
sample_movies = [
    {
        "title": "The Dark Knight",
        "director": "Christopher Nolan",
        "year": "2008",
        "image": "images/dark-knight.jpg"
    },
    {
        "title": "Interstellar",
        "director": "Christopher Nolan",
        "year": "2014",
        "image": "images/interstellar.jpg"
    },
    {
        "title": "Oppenheimer",
        "director": "Christopher Nolan",
        "year": "2023",
        "image": "images/oppenheimer.jpg"
    }
]


# ==================== API TEMPLATE FUNCTIONS ====================
# These functions are placeholders for future API integration

def get_movie_data(movie_id):
    """
    Fetch movie metadata from external API.
    
    Future implementation will call actual movie database API.
    Returns: {title, director, year}
    
    Args:
        movie_id: Identifier for the movie (could be IMDB ID, TMDB ID, etc.)
    
    Returns:
        dict: Movie metadata including title, director, and year
    """
    # PLACEHOLDER - Replace with actual API call
    # Example API: TMDB, OMDB, or similar
    # response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}")
    # return response.json()
    
    return {
        "title": "Movie Title",
        "director": "Director Name",
        "year": "2024"
    }


def get_movie_poster(movie_title):
    """
    Fetch movie poster image URL from external API.
    
    Future implementation will call actual poster API.
    
    Args:
        movie_title: Title of the movie to search for
    
    Returns:
        str: URL of the movie poster image
    """
    # PLACEHOLDER - Replace with actual API call
    # Example: TMDB poster API
    # response = requests.get(f"https://api.themoviedb.org/3/search/movie?query={movie_title}")
    # poster_path = response.json()['results'][0]['poster_path']
    # return f"https://image.tmdb.org/t/p/w500{poster_path}"
    
    return "images/placeholder.jpg"


def get_recommendations_from_gemini(user_movies):
    """
    FUTURE FUNCTION - Get movie recommendations from Google Gemini API.
    
    This function is a placeholder for future implementation.
    
    Flow:
    1. Google Gemini API generates 10 movie recommendations
    2. App selects top 3
    3. For each movie:
       - Call get_movie_data() for metadata
       - Call get_movie_poster() for poster
    4. Return formatted movie list
    
    Args:
        user_movies: List of movies the user has watched/liked
    
    Returns:
        list: List of recommended movies with full metadata
    """
    # PLACEHOLDER - Do NOT implement yet
    # Will integrate with Google Gemini API later
    pass


# ==================== ROUTES ====================

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle CSV file upload and parse its contents"""
    
    # Check if file is present in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if filename is empty
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    try:
        # Read file content as text
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        return parse_csv(csv_reader)
    
    except Exception as e:
        return jsonify({'error': f'Failed to parse CSV: {str(e)}'}), 500


def parse_csv(raw_file):
    """Parse CSV file and return movie data"""
    rows = list(raw_file)
    if not rows:
        return jsonify({'error': "NO DATA IN CSV"}), 400

    # Parse CSV data
    parsed_data = []
    for row in rows:
        parsed_data.append({
            'date': row.get('Date', ''),
            'name': row.get('Name', ''),
            'year': row.get('Year', ''),
            'letterboxd_uri': row.get('Letterboxd URI', '')
        })
    
    return jsonify({
        'message': 'CSV uploaded and parsed successfully',
        'rows': len(parsed_data),
        'data': parsed_data
    }), 200


@app.route('/api/click', methods=['POST'])
def track_click():
    """
    Track when a user clicks on a movie card.
    Stores movie data for future Google Gemini API integration.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Extract movie info
    movie_info = {
        "title": data.get('title', ''),
        "director": data.get('director', ''),
        "year": data.get('year', '')
    }
    
    # Add to clicked movies list
    clicked_movies.append(movie_info)
    
    print(f"[CLICK TRACKED] {movie_info['title']} ({movie_info['year']}) - Director: {movie_info['director']}")
    print(f"[TOTAL CLICKS] {len(clicked_movies)} movies tracked")
    
    return jsonify({
        'success': True,
        'message': f"Tracked: {movie_info['title']}",
        'total_clicks': len(clicked_movies)
    }), 200


@app.route('/api/clicked-movies', methods=['GET'])
def get_clicked_movies():
    """Return all clicked movies (for debugging/future use)"""
    return jsonify({
        'clicked_movies': clicked_movies,
        'count': len(clicked_movies)
    }), 200


@app.route('/api/movies', methods=['GET'])
def get_movies():
    """
    Return movie data for the recommendation page.
    Currently returns sample data, will be replaced by API data.
    """
    return jsonify({
        'movies': sample_movies
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Simple endpoint to check if server is running"""
    return jsonify({'status': 'Flask server is running'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
