# FrameFinderLE

FrameFinderLE is an advanced image and video frame retrieval system that enhances CLIP's image-text pairing capabilities with hashtag-based refinement and sophisticated user feedback mechanisms, providing an intuitive and flexible search experience.

## Table of Contents
- [FrameFinderLE](#framefinderle)
  - [Table of Contents](#table-of-contents)
  - [Motivation and Contribution](#motivation-and-contribution)
    - [Problem Addressed](#problem-addressed)
    - [Our Solution](#our-solution)
    - [Key Contributions](#key-contributions)
  - [System Overview](#system-overview)
  - [Key Features](#key-features)
  - [Technical Details](#technical-details)
    - [Immediate Feedback System](#immediate-feedback-system)
    - [Aggregated Feedback System](#aggregated-feedback-system)
  - [Installation](#installation)
  - [Directory Structure](#directory-structure)
  - [Usage](#usage)
  - [Contributing](#contributing)
  - [License](#license)

## Motivation and Contribution

FrameFinderLE addresses the limitations of traditional image retrieval systems, particularly when dealing with the complexities of human memory and imprecise queries.

### Problem Addressed
- CLIP's 77-token limit restricts complex or detailed queries
- Human memory and recall are often fragmented and imprecise
- Traditional systems struggle with partial or imperfect user input

### Our Solution
FrameFinderLE overcomes these challenges by:
1. **Extended Descriptions**: Combining longer descriptions with traditional prompts to accommodate less precise inputs.
2. **Hashtag Integration**: Allowing users to gradually refine their search using key terms, aligning with natural recall patterns.
3. **Flexible Search System**: Creating an intuitive interface that matches how users naturally remember events and scenes.

### Key Contributions
- Bridges computer vision, natural language processing, and human-computer interaction
- Advances cognitive computing by adapting to the fluid and imperfect nature of human recall
- Enhances retrieval experiences and contributes to more advanced human-computer interaction models

## System Overview

![FrameFinderLE's diagram](./diagram/FrameFinderLE_fw_v1.png)

## Key Features

1. **CLIP Integration**: Utilizes CLIP's powerful image-text pairing capabilities as the foundation of the retrieval system.
2. **Hashtag-Based Refinement**: Allows users to narrow results using partial details or key terms.
3. **Dual Feedback Systems**:
   - **Immediate Feedback System**: Rapidly refines search results based on user likes and dislikes within the current session.
   - **Aggregated Feedback System**: Provides long-term refinement by incorporating historical feedback and balancing exploration with exploitation.
4. **Similarity-Based Score Adjustment**: Utilizes encoded frame representations to adjust scores based on similarities between liked/disliked items and other results.
5. **Relevant Lookup Feature**: Enables new searches based on any result image, creating a more interactive and personalized experience.
6. **VideoID and Timestamp Filters**: Helps users find adjacent frames when searching for specific moments in video clips.
7. **Multi-Modal Search**: Supports text queries, hashtags, and combinations for flexible searching.

## Technical Details

### Immediate Feedback System

The Immediate Feedback System in FrameFinderLE provides rapid refinement of search results based on user interactions within the current session. Here's how it works:

1. **Feedback Processing**: 
   - User feedback (likes, dislikes, neutral) is converted to a binary representation.
   - The system uses pre-encoded representations of database entries (frames) for efficient similarity calculations.

2. **Score Adjustment**:
   - For liked items, the system increases the scores of similar items in the result set.
   - For disliked items, the system decreases the scores of similar items.
   - Neutral feedback does not affect scores.

3. **Similarity-Based Refinement**:
   - The system calculates similarities between the feedback item and all other items in the current result set.
   - Score adjustments are weighted based on these similarity calculations.

4. **Real-time Updates**:
   - Scores are updated immediately after each piece of feedback, allowing for rapid refinement of results within the session.

5. **Final Refinement**:
   - After processing all feedback, the system sorts the updated scores and returns a refined list of results.

This system allows FrameFinderLE to provide instant, personalized refinements to search results based on user interactions, enhancing the user experience and the relevance of returned items.

### Aggregated Feedback System

The Aggregated Feedback System in FrameFinderLE is a complex mechanism that refines search results based on user interactions. Here's how it works:

1. **Feedback Processing**: 
   - User feedback (likes, dislikes, neutral) is converted to a binary form.
   - A feedback factor is calculated, considering recent interactions more heavily (using a decay factor and time weighting).

2. **Score Adjustment**:
   - Scores are adjusted based on the feedback factor.
   - Positive feedback increases scores, negative feedback decreases scores, and neutral feedback has no effect.

3. **Exploration vs. Exploitation**:
   - An exploration ratio parameter balances showing new, potentially interesting results (exploration) with refining based on known preferences (exploitation).
   - This helps prevent filter bubbles and allows users to discover diverse content.

4. **Time-Sensitive Refinement**:
   - Recent feedback is given more weight than older feedback, allowing the system to adapt to changing user preferences over time.

5. **Final Refinement**:
   - Adjusted scores are combined with original relevance scores.
   - Results are re-ranked based on these final scores.

This system allows FrameFinderLE to provide personalized, relevant results that improve over time with user interaction, while still maintaining diversity in the recommendations.

## Installation

[Updating]

## Directory Structure

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
├── database/
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


"""

## Usage

[Updating...
1. How to start the system
2. Examples of different types of queries (text, hashtags, combinations)
3. How to use the immediate and aggregated feedback systems
4. Explanation of how user feedback influences current and future searches
5. Tips for effective searching and result refinement]

## Contributing

[Updating]

## License

[Updating]