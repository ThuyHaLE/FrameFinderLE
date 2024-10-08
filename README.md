# FrameFinderLE

FrameFinderLE is an advanced image and video frame retrieval system that enhances CLIP's image-text pairing capabilities with hashtag-based refinement and sophisticated user feedback mechanisms, providing an intuitive and flexible search experience.

## Table of Contents
- [Motivation and Contribution](#motivation-and-contribution)
- [System Overview](#system-overview)
- [Key Features](#key-features)
- [Technical Details](#technical-details)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Motivation and Contribution

[This section remains the same as in the previous version]

## System Overview

[Include a brief description and the system diagram here. You can reference the detailed flowchart provided earlier, explaining the main components: Database Design, Front-end, and Back-end.]

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

[This section remains the same as in the previous version]

## Installation

[Provide step-by-step installation instructions here. Include any dependencies, environment setup, and configuration steps.]

## Usage

[Provide detailed usage instructions here. You might want to include:
1. How to start the system
2. Examples of different types of queries (text, hashtags, combinations)
3. How to use the immediate and aggregated feedback systems
4. Explanation of how user feedback influences current and future searches
5. Tips for effective searching and result refinement]

## Contributing

[This section remains the same as in the previous version]

## License

[This section remains the same as in the previous version]# FrameFinderLE

FrameFinderLE is an advanced image and video frame retrieval system that enhances CLIP's image-text pairing capabilities with hashtag-based refinement and sophisticated user feedback mechanisms, providing an intuitive and flexible search experience.

## Table of Contents
- [Motivation and Contribution](#motivation-and-contribution)
- [System Overview](#system-overview)
- [Key Features](#key-features)
- [Technical Details](#technical-details)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Motivation and Contribution

[This section remains the same as in the previous version]

## System Overview

[Include a brief description and the system diagram here. You can reference the detailed flowchart provided earlier, explaining the main components: Database Design, Front-end, and Back-end.]

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

[This section remains the same as in the previous version]

## Installation

[Provide step-by-step installation instructions here. Include any dependencies, environment setup, and configuration steps.]

## Usage

[Provide detailed usage instructions here. You might want to include:
1. How to start the system
2. Examples of different types of queries (text, hashtags, combinations)
3. How to use the immediate and aggregated feedback systems
4. Explanation of how user feedback influences current and future searches
5. Tips for effective searching and result refinement]

## Contributing

[This section remains the same as in the previous version]

## License

[This section remains the same as in the previous version]