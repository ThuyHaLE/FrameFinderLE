# ⚡FrameFinderLE⚡

FrameFinderLE is an advanced image and video frame retrieval system that improves real-world memory-driven search tasks. Originally inspired by the challenge of visual information retrieval in noisy, fragmented queries (e.g., user memory recall), it enhances CLIP with hashtag graphs and human-in-the-loop feedback mechanisms.   

## ⚡Table of Contents
- [FrameFinderLE](#framefinderle)
  - [Table of Contents](#table-of-contents)
  - [Motivation and Contribution](#motivation-and-contribution)
    - [Problem Addressed](#problem-addressed)
    - [My Solution](#my-solution)
    - [Key Contributions](#key-contributions)
  - [System Overview](#system-overview)
  - [Key Features](#key-features)
    - [GRAFA Retrieval Mechanism](#grafa-retrieval-mechanism)
    - [Immediate Feedback System](#immediate-feedback-system)
    - [Aggregated Feedback System](#aggregated-feedback-system)
  - [Directory Structure](#directory-structure)
  - [Usage](#usage)
    - [How to start the application](#how-to-start-the-application)
    - [DEMO video](#demo-video)
    - [Database preparation](#database-preparation)
    - [Google colab demo](#google-colab-demo)
  - [Valuation metrics](#valuation-metrics)
  - [Limitations](#limitations)
  - [Contributing](#contributing)
  - [License](#license)

## ⚡Motivation and Contribution

FrameFinderLE addresses the limitations of traditional image retrieval systems, particularly when dealing with the complexities of human memory and imprecise queries.

### 🐳Problem Addressed
- CLIP's 77-token limit restricts complex or detailed queries
- Human memory and recall are often fragmented and imprecise
- Traditional systems struggle with partial or imperfect user input

### 🐳My Solution
FrameFinderLE overcomes these challenges by:
1. **Extended Descriptions**: Combining longer descriptions with traditional prompts to accommodate less precise inputs.
2. **Hashtag Integration**: Allowing users to gradually refine their search using key terms, aligning with natural recall patterns.
3. **Flexible Search System**: Creating an intuitive interface that matches how users naturally remember events and scenes.

### 🐳Key Contributions
- Bridges computer vision, natural language processing, and human-computer interaction
- Advances cognitive computing by adapting to the fluid and imperfect nature of human recall
- Enhances retrieval experiences and contributes to more advanced human-computer interaction models

## ⚡How FrameFinderLE Goes Beyond CLIP
- CLIP is limited to short text and lacks context handling
- FrameFinderLE adds:
   - Graph-based hashtag expansion (GRAFA)
   - Real-time & historical user feedback learning
   - Frame-to-frame similarity scoring for multi-modal refinement

     
## ⚡System Overview

![FrameFinderLE's diagram](https://github.com/ThuyHaLE/FrameFinderLE/blob/main/diagram/FrameFinderLE_diagram.png)

## ⚡Key Features

1. **CLIP Integration**: Utilizes CLIP's powerful image-text pairing capabilities as the foundation of the retrieval system.
2. **Hashtag-Based Refinement**: Allows users to narrow results using partial details or key terms.
3. **Dual Feedback Systems**:
   - **Immediate Feedback System**: Rapidly refines search results based on user likes and dislikes within the current session.
   - **Aggregated Feedback System**: Provides long-term refinement by incorporating historical feedback and balancing exploration with exploitation.
4. **Similarity-Based Score Adjustment**: Utilizes encoded frame representations to adjust scores based on similarities between liked/disliked items and other results.
5. **Relevant Lookup Feature**: Enables new searches based on any result image, creating a more interactive and personalized experience.
6. **VideoID and Timestamp Filters**: Helps users find adjacent frames when searching for specific moments in video clips.
7. **Multi-Modal Search**: Supports text queries, hashtags, and combinations for flexible searching.

### 🐳GRAFA Retrieval Mechanism
The Dynamic Hashtag Exploration in GRAFA is a graph-based retrieval mechanism that discovers and ranks keyframes based on relationships between hashtags. Here's how it works:
1. Hashtag Exploration:
   - Query Initialization: Starts with the provided query hashtags and their embeddings.
   - Graph Traversal: The hashtag co-occurrence graph is traversed to explore neighboring hashtags, capturing broader context while maintaining focus on relevant terms.
2. Scoring System:
   - Hybrid Score Calculation: Combines neighbor frequency and path length to score hashtags.
   - Logarithmic Path Adjustment: Prevents score inflation from repetitive paths by logarithmic scaling.
3. Dynamic Exploration:
   - Prioritizes hashtags with scores above the mean and adjusts exploration depth based on relevance.
4. Stopping Criteria:
   - Stops exploration based on reaching a defined number of keyframes, iterations, or a score threshold.
5. Keyframe Ranking:
   - Normalizes scores and ranks the top keyframes based on their final scores, retrieving the most relevant frames.
  
### 🐳Immediate Feedback System
The Immediate Feedback System provides rapid refinement of search results based on user interactions in the current session.
1. Feedback Processing: Converts user feedback (likes, dislikes) into binary representation and uses pre-encoded frame representations for similarity calculations.
2. Score Adjustment: Adjusts scores based on feedback, increasing for similar liked items and decreasing for similar disliked items.
3. Similarity-Based Refinement: Scores are weighted by similarity to feedback items.
4. Real-time Updates: Scores update immediately after each feedback interaction.
5. Final Refinement: The refined results are re-sorted and returned.

### 🐳Aggregated Feedback System
The Aggregated Feedback System refines searches by incorporating historical feedback for long-term personalized results.
1. Feedback Processing: Converts feedback into a binary form and applies a time-weighted decay factor for recent interactions.
2. Score Adjustment: Adjusts scores based on the feedback factor, balancing exploration with exploitation.
3. Time-Sensitive Refinement: Recent feedback has more influence, adapting to changing preferences.
4. Final Refinement: Combines adjusted scores with original relevance for re-ranked results.

## ⚡Directory Structure

```
/FrameFinderLE/
│
├── database/
│   ├── encoded_frames.pt
│   ├── index_caption_hashtag_dict_v2.json
│   ├── key_frame_folder_reduced.zip
│   ├── merged_index_hnsw_baseline_v0.bin
│   ├── merged_index_hnsw_baseline_v2.bin
│   ├── graph_data_full.pkl
│   ├── hashtag_embeddings.pkl
│   ├── hashtag_embeddings.bin
│   ├── __init__.py
│   └── db_init.py
│
├── diagram/
│   └── FrameFinderLE_diagram.png
│
├── models/
│   ├── __init__.py
│   └── model_init.py
│
├── routers/
│   ├── __init__.py
│   ├── data_router.py
│   ├── feedback_router.py
│   ├── home_router.py
│   ├── process_query_router.py
│   ├── search_router.py
│   └── update_results_router.py
│
├── static/
|   ├── script/
|   │   ├── home_script.js
|   │   ├── popup_mess_script.js
|   │   ├── show_results_script.js
|   │   └── update_results_script.js
│   ├── style/
|   │   ├── home_style.js
|   │   ├── popup_mess.js
|   │   └── show_results_style.js
│   └── images/
│       └── key_frame_folder_reduced/
│           ├── key_frame_folder_videos-l01
│           │   ├── keyframe_L01_V001
│           │   │   ├── 0000161_6.44.webp
│           │   │   ├── 0000350_13.98.webp
│           │   │   └── ...
│           │   └── ...
│           ├── key_frame_folder_videos-l02
│           │   ├── keyframe_L02_V002
│           │   │   ├── 0000010_0.35.webp
│           │   │   ├── 0000040_1.3165.webp
│           │   │   └── ...
│           │   └── ...
│           └── ...
│
├── templates/
│   ├── data.html
│   ├── home.html
│   ├── layout.html
│   ├── results_content.html
│   ├── show_results.html
│   └── v0_search_results.html
│
├── tools/
│   ├── __init__.py
│   ├── aggregated_refining.py
│   ├── faiss_retrieval.py
│   ├── feedback_processing.py
│   ├── graph_based_image_retrieval.py
│   ├── hashtags_generating.py
│   ├── hashtags_processing.py
│   ├── immediate_refining.py
│   ├── info_extracting.py
│   ├── query_encoding.py
│   ├── results_display.py
│   ├── search_utils.py
│   └── utils.py
│
├── __init__.py
├── app_notebook.ipynb
├── app.py
├── README.md
└── requirements.txt
```

## ⚡Usage

### 🐳How to start the application

1. Running the Application with Docker (via Docker Hub)
- Prerequisites: Install Docker on your machine.
- Steps:
```
Pull the Docker image from Docker Hub:
docker pull thuyhale/frame_finder_le:latest
```
```
Run the Docker container:
docker run -p 8000:8000 thuyhale/frame_finder_le:latest
```
```
Open your browser and navigate to:
http://localhost:8000
```

2. Running the Application without Docker
- Prerequisites: 
  - Install Python 3.9 or higher.
  - Install pip.
  - (Optional) Set up a virtual environment.
- Steps:
```
Clone the repository:
git clone https://github.com/ThuyHaLE/FrameFinderLE.git
cd FrameFinderLE
```
```
Install the required dependencies:
pip install -r requirements.txt
```
```
Load database

import gdown

#Load and unzip images, store at static/images
gdown 1-92UIqmQ5ODeZlSQ61cjFmUdLVZZ_HfV #Load key frame folder (key_frame_folder_reduced.zip)
unzip -q key_frame_folder_reduced.zip -d static/images #Unzip key frame folder (key_frame_folder_reduced)

#Load database, store at database/
cd FrameFinderLE/database
#Load FAISS
gdown 1-CDUlIAIYAk5L87tXlYFosbUXQQANam8 #Load annotation (index_caption_hashtag_dict_v2.json)
gdown 1EvNEWTNPe8Tk20-Tn0O6BwAgURLJTHZP #Load database CLIP_v0 (merged_index_hnsw_baseline_v0.bin)
gdown 1-85d-oCWU39o9d8Ie0c5093fKTp0IpwO #Load database CLIP_v2 (merged_index_hnsw_baseline_v2.bin)

#Load GRAFA
gdown 1-AotePkVml3iQONPxCZeK-gDjQFI0Asb #Graph database (graph_data_full.pkl)
gdown 1ZRt1-qvJP2CJcWzGykWQVN9JLHBS5XFR #List of hashtag embeddings (hashtag_embeddings.pkl)
gdown 1tZyr1h8yDJO_CXuMn5ounEEdiFKD530d #List of hashtag embeddings (hashtag_embeddings.bin)

gdown 1-KQx8lD7tHJH-RpbLE9gUBA8k_VV5fsI #Load encoded frames
```
```
Run the application:
uvicorn app:app --reload
```
```
Open your browser and navigate to:
http://localhost:8000
```

### 🐳Database preparation
[Updating...]

### 🐳DEMO video
You can see a demo of FrameFinderLE here:
👉 DEMO Video Link [Updating...]

### 🐳Google colab demo
A Colab demo is also available here [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ThuyHaLE/FrameFinderLE/blob/main/app_notebook.ipynb#scrollTo=2PHZE_QQXkfx) to test the model without local setup.

## ⚡Valuation Metrics
I evaluate the system based on the following metrics in both cases:

- **Relevance**: The degree of relevance of the returned results to the user's query.
- **User Feedback**: User interaction with the results through Like and Dislike.
- **Top-k Relevance**: The relevance of the results in the Top 1 and Top 5 to the query.
- **Query Length**: Classification of queries by length: Single Sentence Query and Multiple Sentence Query.
  - Single Sentence Queries: A complete sentence (e.g., "A person running on the beach").
  - Multiple Sentence Queries: A longer input consisting of multiple related or unrelated sentences (e.g., "A person running on the beach. The sky is clear, and the waves are calm.").

I will divide the results into two cases:

## 1. Default Case

In this case, the user performs a query and receives results without any interaction. Metrics are collected based solely on the default results from the system.

| Query Type         | Mode             | Average Top 1 Relevance | Average Top 5 Relevance | User Feedback (Like %) | User Feedback (Dislike %) |
|--------------------|------------------|-------------------------|-------------------------|------------------------|---------------------------|
| Single Sentence    | Query-Only       | ?                   | ?                   | ?%                     | ?%                        |
| Single Sentence    | Query + Hashtags | ?                   | ?                   | ?%                     | ?%                        |
| Multiple Sentences | Query-Only       | ?                   | ?                   | ?%                     | ?%                        |
| Multiple Sentences | Query + Hashtags | ?                   | ?                   | ?%                     | ?%                        |

## 2. Interactive Case

In this case, the user interacts with the results returned by the system by clicking Like or Dislike. After each interaction, the system adjusts the results to better align with the user's preferences. The metrics in the table below will track user interactions and changes in results.

| Query Type         | Mode             | Average Top 1 Relevance | Average Top 5 Relevance | User Feedback (Like %) | User Feedback (Dislike %) |
|--------------------|------------------|-------------------------|-------------------------|------------------------|---------------------------|
| Single Sentence    | Query-Only       | ?                   | ?                   | ?%                    | ?%                       |
| Single Sentence    | Query + Hashtags | ?                   | ?                   | ?%                    | ?%                       |
| Multiple Sentences | Query-Only       | ?                   | ?                   | ?%                    | ?%                       |
| Multiple Sentences | Query + Hashtags | ?                   | ?                   | ?%                    | ?%                       |

Note: The queries and hashtags used in these experiments are fixed across all trials. This means that every experiment uses the same [set of queries](https://github.com/ThuyHaLE/FrameFinderLE/blob/main/diagram/FrameFinderLE_diagram.png), ensuring that evaluations based on the feedback from a single user are meaningful and comparable. Keeping these factors constant helps minimize variability in the results and allows for accurate comparisons between different methods.

## ⚡Limitations

- **Lack of Comparison Between VLM Versions**: The system currently uses the LLava model to extract data, but there is no comparison with other VLM models. This may affect the quality of the results when queries do not match the idea in the database.
- **Keyframe Quality**: The quality of keyframes extracted from videos may affect the final results, as they are extracted using the Pysence detect method.
- **Vietnamese Language Support**: The system does not fully support Vietnamese, which may impact the quality of processing queries in Vietnamese.
- **Limited Comparison Based on Default Hashtags**: Hashtags are automatically generated from the query, and users can edit them. However, we currently only compare the results using the default set of hashtags, without considering any user modifications.
- **Evaluation with a Single User**: Although the results are currently evaluated based on a single user, we acknowledge that results may vary with multiple users. This will be an important factor when evaluating the system's effectiveness in a real-world environment.

## ⚡Contributing

We welcome ideas, testing, or discussions. Please open an issue or pull request.

## ⚡License

This project is licensed under the Apache License 2.0 - see the [LICENSE](https://github.com/ThuyHaLE/FrameFinderLE/blob/main/LICENSE) file for details.
