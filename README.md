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
[Updating...]
![FrameFinderLE Demo](https://github.com/ThuyHaLE/FrameFinderLE/blob/main/assets/demo.gif)

## ⚙️ Quickstart
### Try it on Google Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ThuyHaLE/FrameFinderLE/blob/main/app_notebook.ipynb#scrollTo=2PHZE_QQXkfx)

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
