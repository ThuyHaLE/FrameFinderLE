// Initialize allImages array when the page loads
document.addEventListener('DOMContentLoaded', () => {
    allImages = Array.from(document.querySelectorAll('.gallery-item')).map(item => ({
        src: item.querySelector('img').src,
        videoID: item.getAttribute('data-video-id'),
        frameID: item.getAttribute('data-frame-id'),
        timestamp: item.getAttribute('data-timestamp'),
        dbIdx: item.getAttribute('data-db-idx')
    }));
});

////////////////////////////////////////hahstags////////////////////////////////////////
/**
 * Initializes the hashtags when the page loads.
 */
window.onload = function() {
    updateHashtags(); // Call the function to update hashtags on page load.
};

/**
 * Updates the hashtags displayed based on the value of the hidden input field.
 */
function updateHashtags() {
    console.log('Updating hashtags...');
    const hiddenHashtags = document.getElementById('hiddenHashtags').value; // Get the hidden hashtags value.
    const hashtags = hiddenHashtags ? hiddenHashtags.split(',') : []; // Split the hashtags into an array.
    renderHashtags(hashtags); // Render the hashtags.
}

/**
 * Renders the hashtags as buttons in the container.
 * @param {string[]} hashtags - The array of hashtags to render.
 */
function renderHashtags(hashtags) {
    console.log('Rendering hashtags:', hashtags);
    const container = document.getElementById('hashtagsContainer');
    container.innerHTML = ''; // Clear existing hashtags.

    hashtags.forEach(tag => {
        const button = document.createElement('button');
        button.className = 'hashtag-item'; // Set the class for styling.
        button.innerHTML = `${tag}<span class="hashtag-remove-icon">x</span>`; // Set the button content.
        button.onclick = () => removeHashtag(tag); // Set the onclick handler for removing the hashtag.
        container.appendChild(button); // Append the button to the container.
    });
}

/**
 * Removes a hashtag from the hidden input field and updates the display.
 * @param {string} tagToRemove - The hashtag to remove.
 */
function removeHashtag(tagToRemove) {
    const hiddenHashtags = document.getElementById('hiddenHashtags');
    const hashtags = hiddenHashtags.value.split(',').filter(tag => tag !== tagToRemove); // Remove the hashtag from the array.

    hiddenHashtags.value = hashtags.join(','); // Update the hidden input field.
    renderHashtags(hashtags); // Re-render the hashtags.
}

////////////////////////////////////////image modal////////////////////////////////////////
// Global variables to keep track of current image index and all images
let currentImageIndex = 0;
let allImages = [];
let currentDbIdx = null;

/** 
 * Opens a modal with the provided image and metadata. 
 * @param {string} imagePath - The path to the image to display. 
 * @param {string} videoID - The ID of the video. 
 * @param {string} frameID - The ID of the frame. 
 * @param {string} timestamp - The timestamp of the frame. 
 */ 
// Modify openModal to initialize allImages based on current page items
function openModal(imagePath, videoID, frameID, timestamp, dbIdx) { 
    const modal = document.getElementById('myModal'); 
    const modalImage = document.getElementById('modalImage'); 
    const modalIndex = document.getElementById('modalIndex'); 
    
    modalImage.src = imagePath; // Set the image source. 
    modalIndex.innerText = `Video ID: ${videoID} | Frame ID: ${frameID} | Timestamp: ${timestamp}`; // Set the metadata text. 
    modal.classList.add('show'); // Add class to trigger zoom-in effect. 
    modal.style.display = 'block'; // Show the modal. 
    
    // Initialize allImages for the current page
    allImages = Array.from(document.querySelectorAll('.gallery-item')).map(item => ({
        src: item.querySelector('img').src,
        videoID: item.getAttribute('data-video-id'),
        frameID: item.getAttribute('data-frame-id'),
        timestamp: item.getAttribute('data-timestamp'),
        dbIdx: item.getAttribute('data-db-idx')
    }));

    // Find the index of the current image
    currentImageIndex = allImages.findIndex(img => img.src === imagePath);
    currentDbIdx = dbIdx;  // Store the current dbIdx
    
    // Add event listeners for keyboard navigation
    document.addEventListener('keydown', handleKeyPress);
    
    // Add event listener to close modal when clicking outside the image. 
    modal.addEventListener('click', outsideClickListener);

    // Update the search button's onclick function
    updateSearchButton();
}

/**
 * Updates the search button's onclick function with the current dbIdx
 */
function updateSearchButton() {
    const searchButton = document.getElementById('searchButton');
    if (searchButton) {
        searchButton.onclick = function() {
            searchByImage();
        };
    }
}

/** 
 * Initiates a search based on the current image. 
 */ 
function searchByImage() {
    console.log("Searching with dbIdx:", currentDbIdx); // Debug log
    if (currentDbIdx === null || currentDbIdx === undefined) {
        console.error("No valid dbIdx found");
        alert("Sorry, we couldn't find a valid image index. Please try selecting an image again.");
        return;
    }
    fetch(`/search/${currentDbIdx}`)
        .then(response => response.text())
        .then(html => {
            // Open a new window/tab and write the HTML content to it
            const newWindow = window.open('', '_blank');
            newWindow.document.write(html);
            newWindow.document.close();
        })
        .catch(error => {
            console.error('Error fetching search results:', error);
            alert('An error occurred while fetching search results. Please try again.');
        });
}

/** 
 * Closes the modal. 
 */ 
function closeModal() { 
    const modal = document.getElementById('myModal'); 
    modal.classList.remove('show'); // Remove the class that triggers the zoom-in effect. 
    modal.style.display = 'none'; // Hide the modal. 
    
    // Remove event listeners
    document.removeEventListener('keydown', handleKeyPress);
    modal.removeEventListener('click', outsideClickListener);
}

/** 
 * Handles key press events for navigation. 
 * @param {KeyboardEvent} event - The keyboard event. 
 */ 
function handleKeyPress(event) {
    if (event.key === 'ArrowLeft') {
        showPreviousImage();
    } else if (event.key === 'ArrowRight') {
        showNextImage();
    } else if (event.key === 'Escape') {
        closeModal();
    }
}

/** 
 * Shows the next image in the modal. 
 */ 
function showNextImage() {
    if (currentImageIndex < allImages.length - 1) {
        currentImageIndex++;
        updateModalImage();
    }
}

/** 
 * Shows the previous image in the modal. 
 */ 
function showPreviousImage() {
    if (currentImageIndex > 0) {
        currentImageIndex--;
        updateModalImage();
    }
}

/**
 * Updates the modal with the current image and its metadata.
 */
function updateModalImage() {
    const currentImage = allImages[currentImageIndex];
    const modalImage = document.getElementById('modalImage');
    const modalIndex = document.getElementById('modalIndex');
    
    modalImage.src = currentImage.src;
    modalIndex.innerText = `Video ID: ${currentImage.videoID} | Frame ID: ${currentImage.frameID} | Timestamp: ${currentImage.timestamp}`;
    
    // Update the current dbIdx
    currentDbIdx = currentImage.dbIdx;
}

/** 
 * Listens for clicks outside the modal to close it. 
 * @param {Event} event - The click event. 
 */ 
function outsideClickListener(event) { 
    const modal = document.getElementById('myModal'); 
    if (event.target === modal) { 
        closeModal();
    } 
}

// Call this when the page loads
document.addEventListener('DOMContentLoaded', initializeSearchButton);

// Ensure the search button is created only once
function initializeSearchButton() {
    const modalContent = document.querySelector('.modal-content');
    if (!document.getElementById('searchButton')) {
        const searchButton = document.createElement('button');
        searchButton.id = 'searchButton';
        searchButton.innerText = '🔍'; // Set the button text
        searchButton.className = 'search-button'; // Assign class for styling
        modalContent.appendChild(searchButton); // Append button to modal content
    }
}

////////////////////////////////////////user feedbacks////////////////////////////////////////
// Function to generate a unique session ID
function generateSessionId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Global variable to store the current session ID
let currentSessionId = getOrCreateSessionId();

// Function to get or create a session ID
function getOrCreateSessionId() {
    let sessionId = localStorage.getItem('sessionId');
    if (!sessionId) {
        sessionId = generateSessionId();
        localStorage.setItem('sessionId', sessionId);
    }
    return sessionId;
}

// Function to generate a new session ID
function generateNewSessionId() {
    const newSessionId = generateSessionId();
    localStorage.setItem('sessionId', newSessionId);
    return newSessionId;
}

// Reset session ID when the page reloads
document.addEventListener('DOMContentLoaded', () => {
    currentSessionId = generateNewSessionId();
    console.log('New Session ID on page load:', currentSessionId); // Debug log for verification
});


// Object to track user feedbacks
let userFeedbacks = {};

// Initialize the feedback state for an image
function initializeFeedback(db_idx) {
    if (!userFeedbacks[db_idx]) {
        userFeedbacks[db_idx] = 'neutral'; // Initial state
    }
}

// Toggle like feedback
async function toggleLike(db_idx) {
    initializeFeedback(db_idx);

    if (userFeedbacks[db_idx] === 'like') {
        userFeedbacks[db_idx] = 'neutral';
    } else {
        userFeedbacks[db_idx] = 'like';
    }

    updateButtonStyles(db_idx);
    await updateFeedback(db_idx, userFeedbacks[db_idx]);
    await submitAllFeedback();
    await refreshResults();  // Add this line to refresh results
}

// Toggle dislike feedback
async function toggleDislike(db_idx) {
    initializeFeedback(db_idx);

    if (userFeedbacks[db_idx] === 'dislike') {
        userFeedbacks[db_idx] = 'neutral';
    } else {
        userFeedbacks[db_idx] = 'dislike';
    }

    updateButtonStyles(db_idx);
    await updateFeedback(db_idx, userFeedbacks[db_idx]);
    await submitAllFeedback();
    await refreshResults();  // Add this line to refresh results
}

// Function to handle feedback updates
async function updateFeedback(db_idx, action) {
    const params = new URLSearchParams({ 
        db_idx: db_idx, 
        action: action,
        session_id: currentSessionId
    });
    try {
        const response = await fetch('/update_feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: params.toString()
        });
        if (response.ok) {
            const result = await response.json();
            updateFeedbackStatus(db_idx, result.feedbackStatus);
            
            // Update the local userFeedbacks object
            userFeedbacks[db_idx] = action;
            
            // Update UI for the affected item
            updateButtonStyles(db_idx);
        } else {
            console.error('Failed to update feedback');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Function to submit all feedback
async function submitAllFeedback() {
    try {
        const response = await fetch('/submit_feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({ session_id: currentSessionId }).toString()
        });
        if (response.ok) {
            const result = await response.json();
            console.log('Feedback submitted successfully:', result.submittedFeedback);
            
            // Don't clear the local userFeedbacks object here
            // Update UI for all items
            updateAllButtonStyles();
        } else {
            console.error('Failed to submit feedback');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Function to refresh results after feedback
async function refreshResults() {
    const formData = new FormData(document.getElementById('updateForm'));
    formData.set('page', 1);
    formData.set('session_id', currentSessionId);

    const params = new URLSearchParams(formData);
    try {
        const response = await fetch('/update_results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: params
        });
        if (response.ok) {
            const resultHtml = await response.text();
            document.getElementById('results').innerHTML = resultHtml;
            updateURL(1);
        } else {
            console.error('Failed to refresh results');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Function to update button styles
function updateButtonStyles(db_idx) {
    const likeButton = document.getElementById(`like-${db_idx}`);
    const dislikeButton = document.getElementById(`dislike-${db_idx}`);

    if (userFeedbacks[db_idx] === 'like') {
        likeButton.classList.add('active');
        dislikeButton.classList.remove('active');
        likeButton.style.backgroundColor = "green";
        dislikeButton.style.backgroundColor = ""; // Reset dislike button
    } else if (userFeedbacks[db_idx] === 'dislike') {
        dislikeButton.classList.add('active');
        likeButton.classList.remove('active');
        dislikeButton.style.backgroundColor = "red";
        likeButton.style.backgroundColor = ""; // Reset like button
    } else {
        likeButton.classList.remove('active');
        dislikeButton.classList.remove('active');
        likeButton.style.backgroundColor = "";
        dislikeButton.style.backgroundColor = ""; // Reset both buttons
    }
}

function updateAllButtonStyles() {
    for (let db_idx in userFeedbacks) {
        updateButtonStyles(db_idx);
    }
}

// Function to update the feedback status message
function updateFeedbackStatus(db_idx, feedbackStatus) {
    const feedbackStatusElement = document.getElementById(`feedback-status-${db_idx}`);
    if (feedbackStatusElement) {
        feedbackStatusElement.textContent = feedbackStatus;
    }
}

/// Aggregated Feedback System (Adjustment for List of user feedbacks) ///

document.addEventListener('DOMContentLoaded', function() {
    const refineButton = document.getElementById('refinement-btn');
    if (refineButton) {
        refineButton.addEventListener('click', handleRefine);
    }
});

async function handleRefine() {
    const formData = new FormData(document.getElementById('updateForm'));
    formData.set('page', 1);
    formData.set('session_id', currentSessionId);
    formData.set('refine_status', 'True');

    const params = new URLSearchParams(formData);
    try {
        const response = await fetch('/update_results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: params
        });
        if (response.ok) {
            const resultHtml = await response.text();
            document.getElementById('results').innerHTML = resultHtml;
            updateURL(1);
        } else {
            console.error('Failed to refine results');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}