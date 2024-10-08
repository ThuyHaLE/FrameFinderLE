// popup_mess.js

document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.textContent = `
    /* The Modal (background) */
    .modal {
        display: none; /* Hidden by default */
        position: fixed;
        z-index: 1;
        left: 0;
        top: 0;
        width: 100%; /* Full width */
        height: 100%; /* Full height */
        overflow: auto; /* Enable scroll if needed */
        background-color: rgba(0,0,0,0.4); /* Black w/ opacity */
    }

    /* Modal Content/Box */
    .modal-content {
        background-color: #000000; /* Black background */
        color: #ff0000; /* Red text */
        margin: 20% auto; /* 15% from the top and centered */
        padding: 10px;
        border: 1px solid #888;
        width: 30%; /* Could be more or less, depending on screen size */
        box-shadow: 0px 4px 8px rgba(0,0,0,0.2);
        border-radius: 5px;
        position: relative; /* Make the close button position relative to this box */
    }

    /* The Close Button */
    .close-btn {
        color: #ffffff; /* White close button */
        font-size: 25px;
        font-weight: bold;
        position: absolute; /* Position the button absolutely */
        top: 1px; /* Position it 10px from the top */
        right: 5px; /* Position it 15px from the right */
    }

    .close-btn:hover,
    .close-btn:focus {
        color: #ff0000; /* Red close button on hover */
        text-decoration: none;
        cursor: pointer;
    }
    `;
    document.head.appendChild(style);
});