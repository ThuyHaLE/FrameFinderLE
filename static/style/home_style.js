// home_style.js

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
    background-color: #1b1b1b;
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
    color: #ffcc00;
    margin-bottom: 5px;
  }
  .form-group input,
  .form-group select {
    background-color: #333;
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
    color: #ffcc00;
    margin-bottom: 5px;
  }

  .clear-btn {
    background-color: transparent;
    border: 1px solid #ffcc00;
    color: #ffcc00;
    cursor: pointer;
    height: 30px;
    line-height: 30px;
  }
  .clear-btn:hover {
    background-color: #444;
    color: #ffcc00;
  }

  .query-row,
  .hashtag-row {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .query-row input {
    flex-grow: 1;
    margin-right: 10px;
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
    transform: scale(0.9);
    margin-right: 5px;
    width: 15px;
    height: 15px;
  } 
  #clearAllButton {
    height: 30px;
    line-height: 30px;
    padding: 0 20px;
    border: none;
    background-color: #ffcc00;
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
    background-color: #ffcc00;
    color: black;
    border-radius: 5px;
    cursor: pointer;
    font-size: 1rem;
  }
  .btn-primary.submit-btn:hover {
    background-color: #e6b800;
  }
`;

// Create a <style> element
const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = styles;

// Append the <style> element to the head of the document
document.head.appendChild(styleSheet);
