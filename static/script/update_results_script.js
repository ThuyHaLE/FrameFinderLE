/**
 * Handles the form submission to update the results without reloading the page.
 * @param {Event} event - The form submission event.
 */
 
// Function to handle form submission and new retrievals
async function updateResults(event) {
    event.preventDefault();

    // Generate a new session ID for each new retrieval
    currentSessionId = generateNewSessionId();

    // Clear previous feedbacks when starting a new retrieval
    userFeedbacks = {};

    const formData = new FormData(event.target);
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
            
            // Update all button styles to reflect cleared feedbacks
            updateAllButtonStyles();
        } else {
            console.error('Failed to update results');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}


async function changePage(page) {
    const formData = new FormData(document.getElementById('updateForm')); // Create a FormData object from the form.
    formData.set('page', page); // Set the page number in the form data.

    // Add session ID to the form data
    formData.set('session_id', currentSessionId); // Include the current session ID

    const params = new URLSearchParams(formData); // Convert the FormData object to URLSearchParams.
    try {
        const response = await fetch('/update_results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: params // Send the form data to the server.
        });
        if (response.ok) {
            const resultHtml = await response.text(); // Get the HTML response from the server.
            document.getElementById('results').innerHTML = resultHtml; // Update the results container with the new HTML.
            updateURL(page); // Update URL to reflect the new page
        } else {
            console.error('Failed to change page'); // Log an error if the request fails.
        }
    } catch (error) {
        console.error('Error:', error); // Log any errors that occur during the fetch.
    }
}

/**
 * Updates the URL to reflect the current page without reloading.
 * @param {number} page - The current page number.
 */
function updateURL(page) {
    const url = new URL(window.location);
    url.searchParams.set('page', page);
    window.history.pushState({}, '', url);
}