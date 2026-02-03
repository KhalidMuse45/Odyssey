// ==================== MOVIE CARD HANDLING ====================
const cardsContainer = document.getElementById('cardsContainer');
const starAnimation = document.getElementById('starAnimation');

// Sample movies for fallback
const sample_movies = [
  { title: "The Dark Knight", director: "Christopher Nolan", year: "2008", image: "images/dark-knight.jpg" },
  { title: "Interstellar", director: "Christopher Nolan", year: "2014", image: "images/interstellar.jpg" },
  { title: "Oppenheimer", director: "Christopher Nolan", year: "2023", image: "images/oppenheimer.jpg" }
];

// Load movies from API or use fallback
async function loadMovies() {
  try {
    const response = await fetch('http://127.0.0.1:5000/api/movies');
    if (!response.ok) throw new Error('API not available');
    const movies = await response.json();
    renderMovieCards(movies);
  } catch (error) {
    console.log('Using sample movies:', error);
    renderMovieCards(sample_movies);
  }
}

// Render movie cards dynamically
function renderMovieCards(movies) {
  cardsContainer.innerHTML = '';
  
  movies.forEach(movie => {
    const cardWrapper = document.createElement('div');
    cardWrapper.className = 'card-wrapper';
    cardWrapper.dataset.title = movie.title;
    cardWrapper.dataset.director = movie.director;
    cardWrapper.dataset.year = movie.year;
    
    cardWrapper.innerHTML = `
      <div class="product-card">
        <div class="card-image">
          <img src="${movie.image}" alt="${movie.title} poster" onerror="this.style.display='none'">
        </div>
        <div class="card-body">
          <p class="card-title">Title: ${movie.title} (${movie.year})</p>
          <p class="card-subtitle">Director: ${movie.director}</p>
        </div>
      </div>
      <div class="card-action">
        <button class="icon-btn icon-btn-filled favorite-btn" aria-label="Add ${movie.title} to favorites">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
          </svg>
        </button>
      </div>
    `;
    
    cardsContainer.appendChild(cardWrapper);
    
    // Add click handlers
    const productCard = cardWrapper.querySelector('.product-card');
    const favoriteBtn = cardWrapper.querySelector('.favorite-btn');
    
    // Card click handler
    productCard.addEventListener('click', () => {
      if (!favoriteBtn.classList.contains('active')) {
        handleCardClick(movie, cardWrapper);
      }
      favoriteBtn.classList.toggle('active');
    });
    
    // Star button click handler
    favoriteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (!favoriteBtn.classList.contains('active')) {
        handleCardClick(movie, cardWrapper);
      }
      favoriteBtn.classList.toggle('active');
    });
  });
}

let currentAnimatingCard = null;
let starAnimTimeoutId = null;

// Handle card/star click
function handleCardClick(movie, cardWrapper) {
  playStarAnimation(cardWrapper);
  trackMovieClick(movie);
}

// Play star burst animation
// - Clicking the same card again during the animation does nothing
// - Clicking a different card will play immediately (moves the overlay)
function playStarAnimation(cardWrapper) {
  if (!cardWrapper) return;

  // If this same card is already animating, don't restart/cut it off
  if (currentAnimatingCard === cardWrapper && starAnimation.classList.contains('active')) {
    return;
  }

  // If switching cards mid-animation, clean up the previous card state
  if (currentAnimatingCard && currentAnimatingCard !== cardWrapper) {
    currentAnimatingCard.classList.remove('card-clicked');
  }

  currentAnimatingCard = cardWrapper;

  const rect = cardWrapper.getBoundingClientRect();
  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;
  
  starAnimation.style.left = `${centerX}px`;
  starAnimation.style.top = `${centerY}px`;
  
  cardWrapper.classList.add('card-clicked');

  // Restart overlay animation cleanly
  if (starAnimTimeoutId) {
    clearTimeout(starAnimTimeoutId);
    starAnimTimeoutId = null;
  }
  starAnimation.classList.remove('active');
  void starAnimation.offsetWidth;
  starAnimation.classList.add('active');

  starAnimTimeoutId = setTimeout(() => {
    // Only clear if we haven't switched to another card meanwhile
    if (currentAnimatingCard === cardWrapper) {
      starAnimation.classList.remove('active');
      cardWrapper.classList.remove('card-clicked');
      currentAnimatingCard = null;
      starAnimTimeoutId = null;
    }
  }, 1000);
}

// Send click data to Flask backend
async function trackMovieClick(movie) {
  try {
    const response = await fetch('http://127.0.0.1:5000/api/click', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: movie.title,
        director: movie.director,
        year: movie.year
      })
    });
    
    const data = await response.json();
    console.log('Click tracked:', data);
  } catch (error) {
    console.error('Error tracking click:', error);
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  loadMovies();
});
