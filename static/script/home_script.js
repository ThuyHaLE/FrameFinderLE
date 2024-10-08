// Wait for the DOM to be fully loaded before executing the script
    document.addEventListener('DOMContentLoaded', function() {
    // Get references to key DOM elements
    const inputElement = document.getElementById('queryInput');
    const hashtagsContainer = document.getElementById('hashtagsContainer');
    const hiddenHashtags = document.getElementById('hiddenHashtags');
    const clearAllButton = document.getElementById('clearAllButton');
    const clearQueryButton = document.querySelector('.clear-btn');
    const generateHashtagsCheckbox = document.getElementById('generateHashtags');
    const relevanceHashtagsGroup = document.getElementById('relevanceHashtagsGroup');

////////////////////////////////////////hashtags generating////////////////////////////////////////

    // Initialize an empty array to hold the current hashtags
    let hashtags = [];

    // Toggle the visibility of the hashtags container based on the checkbox state
    function toggleHashtagsContainer() {
        relevanceHashtagsGroup.style.display = generateHashtagsCheckbox.checked ? 'block' : 'none';
    }

    // Initialize the visibility of the hashtags container
    toggleHashtagsContainer();

    // Handle the checkbox state change for generating relevance hashtags
    generateHashtagsCheckbox.addEventListener('change', function() {
        toggleHashtagsContainer();
        // If the checkbox is checked and there is a query, fetch hashtags
        if (generateHashtagsCheckbox.checked && inputElement.value.trim()) {
            fetchHashtags(inputElement.value.trim());
        } else {
            // Clear all hashtags if the checkbox is unchecked
            clearAllHashtags();
        }
    });

    // Handle input events in the query text field
    inputElement.addEventListener('input', function() {
        const query = inputElement.value.trim();
        // Fetch hashtags if the checkbox is checked and the query is not empty
        if (generateHashtagsCheckbox.checked && query) {
            fetchHashtags(query);
        } else {
            // Clear hashtags if the query is empty
            clearAllHashtags();
        }
    });

    // Fetch hashtags from the server based on the query text
    function fetchHashtags(query) {
        fetch('/process_query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query_text: query }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Received data:', data); // Debug: Log the received data
            const generatedHashtags = data.hashtags || [];
            console.log('Generated hashtags:', generatedHashtags); // Debug: Log the generated hashtags
            updateHashtags(generatedHashtags);
        })
        .catch(error => console.error('Error:', error)); // Handle any errors from the fetch request
    }

    // Update the displayed hashtags if the new set is different from the current set
    function updateHashtags(newHashtags) {
        console.log('Updating hashtags:', newHashtags); // Debug: Log the hashtags being updated

        // Check if the new hashtags are different from the current ones
        const hasChanged = JSON.stringify(newHashtags) !== JSON.stringify(hashtags);

        if (hasChanged) {
            hashtags = [...new Set(newHashtags)]; // Ensure unique hashtags
            console.log('Updated unique hashtags:', hashtags); // Debug: Log the unique hashtags
            displayHashtags(); // Update the UI
            updateHiddenHashtags(); // Update the hidden input field
        } else {
            console.log('No change in hashtags, skipping update');
        }
    }

    // Display the current set of hashtags in the container
    function displayHashtags() {
        console.log('Displaying hashtags:', hashtags); // Debug: Log the hashtags being displayed
        hashtagsContainer.innerHTML = ''; // Clear existing hashtags
        hashtags.forEach(tag => {
            console.log('Creating element for tag:', tag); // Debug: Log each tag being processed
            // Create a button element for each hashtag
            const tagElement = document.createElement('button');
            tagElement.textContent = tag;
            tagElement.className = 'hashtag-item';
            tagElement.onclick = function() {
                removeHashtag(tag); // Remove the hashtag when clicked
            };

            // Add a remove icon (x) to the button
            const removeIcon = document.createElement('span');
            removeIcon.textContent = 'x';
            removeIcon.className = 'hashtag-remove-icon';
            tagElement.appendChild(removeIcon);

            // Append the hashtag button to the container
            hashtagsContainer.appendChild(tagElement);
        });

        // Create an input field for adding new hashtags
        const inputField = document.createElement('input');
        inputField.type = 'text';
        inputField.id = 'newHashtagInput';
        inputField.placeholder = 'Add new hashtag...';
        inputField.addEventListener('keypress', function(event) {
            // Allow users to add a hashtag by pressing Enter
            if (event.key === 'Enter') {
                event.preventDefault();
                addHashtag();
            }
        });
        hashtagsContainer.appendChild(inputField);
    }

    // Add a new hashtag to the list
    function addHashtag() {
        const inputField = document.getElementById('newHashtagInput');
        let userHashtag = inputField.value.trim();

        // Add a '#' prefix if the user didn't include one
        if (userHashtag && !userHashtag.startsWith('#')) {
            userHashtag = `#${userHashtag}`;
        }

        // Only add the hashtag if it doesn't already exist
        if (userHashtag && !hashtags.includes(userHashtag)) {
            hashtags.push(userHashtag);
            displayHashtags(); // Update the UI with the new hashtag
            updateHiddenHashtags(); // Update the hidden input field
        }
        inputField.value = ''; // Clear the input field after adding
    }

    // Remove a hashtag from the list
    function removeHashtag(tag) {
        hashtags = hashtags.filter(t => t !== tag); // Remove the selected hashtag
        displayHashtags(); // Update the UI
        updateHiddenHashtags(); // Update the hidden input field
    }

    // Clear all hashtags from the list
    function clearAllHashtags() {
        hashtags = []; // Empty the hashtag list
        displayHashtags(); // Update the UI
        updateHiddenHashtags(); // Update the hidden input field
    }

    // Update the hidden input field with the current hashtags
    function updateHiddenHashtags() {
        hiddenHashtags.value = hashtags.join(','); // Join hashtags with commas
    }

    // Add event listener to the "Clear All" button, if it exists
    if (clearAllButton) {
        clearAllButton.addEventListener('click', clearAllHashtags);
    }

    // Add event listener to the "Clear Query" button, if it exists
    if (clearQueryButton) {
        clearQueryButton.addEventListener('click', function() {
            inputElement.value = ''; // Clear the query input field
            clearAllHashtags(); // Clear all hashtags
        });
    } else {
        console.error('Clear Query button not found'); // Log an error if the button is missing
    }

////////////////////////////////////////database updating////////////////////////////////////////
    // Ensure only one database checkbox is selected at a time
    function updateDatabaseSelection() {
        const checkboxes = document.querySelectorAll('input[name="database_name"]');
        checkboxes.forEach(cb => {
            cb.addEventListener('change', function() {
                if (cb.checked) {
                    // Uncheck all other checkboxes if one is selected
                    checkboxes.forEach(otherCb => {
                        if (otherCb !== cb) {
                            otherCb.checked = false;
                        }
                    });
                }
                // Ensure at least one checkbox is always selected
                if (!Array.from(checkboxes).some(cb => cb.checked)) {
                    checkboxes[0].checked = true;
                }
            });
        });
    }

    // Initialize the database selection functionality
      updateDatabaseSelection();
    });