# ⚡ FrameFinderLE

> An advanced memory-driven image & video frame retrieval system, enhancing CLIP with hashtag graphs and human feedback.

## 🚀 Project Overview
- **Timeline**: 25/07/2024 - 29/09/2024
- **Tech Stack**: Python, FastAPI, CLIP, FAISS, Docker, Graph Retrieval
- **Dataset**: AI Challenge 2024 (HCMC)

## 🎯 Motivation
FrameFinderLE is designed to overcome CLIP's limitations in noisy environments by leveraging graph-based hashtag expansion and dynamic user feedback.

## 🔥 Key Features
- Graph-based hashtag expansion (GRAFA)
- Dual Feedback: Real-time and Historical learning
- Frame-to-frame similarity adjustment
- Multi-modal search: Text, Hashtag, Image queries
- VideoID and Timestamp filtering for precise search

## 🎬 Demo
Although the demo does not showcase the refined system based on user feedback, FrameFinderLE allows users to interact with the retrieved images through Like and Dislike buttons on each image in the results. These feedbacks are used to refine the search results, enhancing the system's accuracy and better aligning it with user preferences. As users provide feedback, the system dynamically adjusts the search results to reflect these interactions, continuously optimizing the retrieval process.

![FrameFinderLE Demo](https://github.com/ThuyHaLE/FrameFinderLE/blob/main/FrameFinderLE-Demo-compressed.gif)

## ⚙️ System Requirements
- **Operating System:** Windows 10/11, MacOS, or Linux
- **CPU:** Minimum 4 cores (8+ cores recommended for better performance)
- **RAM:** Minimum 8GB (16GB+ recommended)
- **Storage:** At least 10GB for database and installation
- **Python:** Python 3.9 or higher
- **Internet Connection:** Required to download database files

> **Note:** FrameFinderLE is optimized to run on a regular CPU and does not require a GPU.

## ⚙️ Quickstart
### Try it on Google Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ThuyHaLE/FrameFinderLE/blob/main/app_notebook.ipynb#scrollTo=2PHZE_QQXkfx)

> **Note:** You may need to install NLTK and download the 'punkt' dataset to avoid errors.
```
import nltk
nltk.download('punkt_tab')
```

### Run with Docker
```bash
docker pull thuyhale/frame_finder_le:latest
docker run -p 8000:8000 thuyhale/frame_finder_le:latest
```

### Run Locally
```
git clone https://github.com/ThuyHaLE/FrameFinderLE.git
cd FrameFinderLE
pip install -r requirements.txt
python app.py
```

## 📚 Full Documentation
👉 [See Full Documentation Here](https://github.com/ThuyHaLE/FrameFinderLE/blob/main/FULL-README.md)
