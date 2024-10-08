// show_results_style.js

const styles = `
    body {
        background-color: #121212; 
        color: white;
        font-family: Arial, sans-serif;
      }
    .container {
        margin: 1rem;
      }
    h5 {
      color: #ffcc00;
    }
    hr {
      border-color: #333;
    }
    .form-container {
            background-color: #1b1b1b; /* Match with home.html */
            padding: 15px;
            border-radius: 10px;
            margin: 20px auto;
            max-width: 1200px;
        }
    .form-group {
              margin-bottom: 15px;
          }
    .form-group label {
          display: block;
          color: #ffcc00; /* Match with home.html */
          margin-bottom: 5px;
      }
    .form-group input,
      .form-group select {
          background-color: #333; /* Match with home.html */
          color: white;
          border: none;
          border-radius: 5px;
          padding: 5px;
          width: 100%;
          box-sizing: border-box;
          height: 30px;
          line-height: 30px;
      }
    .form-group input::placeholder {
          color: #ccc;
      }
    .form-row {
                display: flex;
                gap: 15px;
                align-items: center;
                flex-wrap: wrap;
            }
    .btn-label {
          font-size: 1rem;
          color: #ffcc00; /* Match with home.html */
          margin-bottom: 5px;
      }
    .btn-primary.submit-btn {
        height: 30px;
        line-height: 30px;
        padding: 0 20px;
        border: none;
        background-color: #ffcc00; /* Match with home.html */
        color: black;
        border-radius: 5px;
        cursor: pointer;
        font-size: 1rem;
    }
    .btn-primary.submit-btn:hover {
        background-color: #e6b800;
    }
    .clear-btn {
          background-color: transparent;
          border: 1px solid #ffcc00;
          color: #ffcc00; /* Match with home.html */
          cursor: pointer;
          height: 30px;
          line-height: 30px;
      }
    .clear-btn:hover {
            background-color: #444; /* Background color on hover */
            color: #ffcc00; /* Keep text color */
        }
    .query-row,
    .hashtag-row {
            display: flex;
            align-items: center;
            gap: 10px;
        }
    .query-row input {
        flex-grow: 1;
        margin-right: 10px; /* Adjust margin as needed */
    }
    #hashtagsContainer {
        display: flex;
        flex-wrap: wrap;
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .hashtag-item {
        display: inline-flex;
        align-items: center;
        padding: 2px 5px;
        margin: 2px;
        background-color: #efefef;
        border-radius: 3px;
        cursor: pointer;
    }
    .hashtag-item .hashtag-remove-icon {
        margin-left: 5px;
        color: red;
        font-weight: bold;
        cursor: pointer;
    }
    .hashtags-checkboxes, 
    .hashtags-label {
        display: flex;
        align-items: center;  
        gap: 10px;
    }
    .hashtags-checkboxes input[type="checkbox"] {
        transform: scale(0.9); /* Adjust the scale to make the checkbox smaller */
        margin-right: 5px; /* Space between checkbox and label */
        width: 15px; /* Optional: Adjust width */
        height: 15px; /* Optional: Adjust height */
    } 
    #clearAllButton {
        height: 30px;
        line-height: 30px;
        padding: 0 20px;
        border: none;
        background-color: #ffcc00; /* Match with home.html */
        color: black;
        border-radius: 5px;
        cursor: pointer;
        font-size: 1rem;  
    }
    .results-container {
        margin-top: 20px;
    }
    .database-checkboxes {
                display: flex;
                gap: 10px;
                align-items: center;
            }
    .database-checkboxes input,
    .database-checkboxes label {
        margin: 0 5px;
      }
    .btn-primary.submit-btn {
            height: 30px;
            line-height: 30px;
            padding: 0 20px;
            border: none;
            background-color: #ffcc00; /* Match with home.html */
            color: black;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
        }
    .btn-primary.submit-btn:hover {
                background-color: #e6b800;
            }
  
    .gallery {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        padding: 10px;
    }
    .gallery-item {
        overflow: hidden;
        position: relative;
        background-color: #222;
        padding: 10px;
        border-radius: 5px;
        cursor: pointer;
    }
    .gallery-item img {
        width: 100%;
        height: auto;
        display: block;
        border-radius: 5px;
    }
    .index-number {
        position: absolute;
        top: 10px;
        left: 10px;
        background-color: rgba(0, 0, 0, 0.5);
        color: #fff;
        padding: 5px;
        border-radius: 5px;
        font-size: 1rem;
        font-weight: bold;
    }
    .pagination {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 20px 0;
    }
    .pagination button {
        padding: 5px 10px;
        margin: 0 10px;
        border: 1px solid #ccc;
        background-color: #f0f0f0;
        cursor: pointer;
    }
    .pagination span {
        margin: 0 10px;
    }
    .pagination button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    /* Modal styles */
    .modal {
        display: none;
        position: fixed;
        z-index: 1000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        overflow: auto;
        background-color: rgba(0, 0, 0, 0.4);
        transition: all 0.3s ease-in-out; /* Smooth transition for modal display */
    }
    .modal-content {
        margin: 5% auto;
        position: relative;
        padding: 20px;
        border: 1px solid #888;
        width: 90%;
        max-width: 700px;
        background-color: black;
        color: white;
        transform: scale(0); /* Start with the image zoomed out */
        transition: transform 0.3s ease-in-out; /* Smooth transition for zoom */
    }
    .modal img {
        width: 100%;
        height: auto;
    }
    .close {
        color: #aaa;
        float: right;
        font-size: 28px;
        font-weight: bold;
    }
    .close:hover,
    .close:focus {
        color: #fff;
        text-decoration: none;
        cursor: pointer;
    }
    .modal.show .modal-content {
        transform: scale(1); /* Zoom in when modal is displayed */
    }
    .navigation-arrows {
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        display: flex;
        justify-content: space-between;
    }
    .nav-arrow {
        background-color: rgba(0, 0, 0, 0.5);
        color: white;
        border: none;
        padding: 10px 15px;
        font-size: 24px;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .nav-arrow:hover {
        background-color: rgba(0, 0, 0, 0.8);
    }

`;
// Create a <style> element
const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = styles;

// Append the <style> element to the head of the document
document.head.appendChild(styleSheet);