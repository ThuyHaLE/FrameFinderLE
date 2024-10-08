// popup_mess_script.js

document.addEventListener('DOMContentLoaded', function() {
    const inputElement = document.getElementById('queryInput');
    const hiddenHashtags = document.getElementById('hiddenHashtags');
    const searchForm = document.getElementById('searchForm');
    const modal = document.getElementById('errorModal');
    const closeModalButton = document.querySelector('.close-btn');

    // Form submission handler
    searchForm.addEventListener('submit', function(event) {
        const query = inputElement.value.trim();
        const hashtagsValue = hiddenHashtags.value.trim();

        // Check if both query and hashtags are empty
        if (!query && !hashtagsValue) {
            event.preventDefault(); // Prevent form submission
            showErrorModal("At least one of query text or hashtags must be provided.");
        }
    });

    // Function to show error modal
    function showErrorModal(message) {
        const messageElement = document.getElementById('errorMessage');
        messageElement.textContent = message;
        modal.style.display = 'block';
    }

    // Function to close error modal
    function closeErrorModal() {
        modal.style.display = 'none';
    }

    // Close modal when clicking outside of the modal-content
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeErrorModal();
        }
    });

    // Make the close button work
    closeModalButton.addEventListener('click', closeErrorModal);
});
