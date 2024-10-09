#!/bin/bash

# Set base project and database paths
PROJECT_PATH=$(pwd)
DATABASE_PATH=$PROJECT_PATH/database

echo "Project directory: $PROJECT_PATH"
echo "Database directory: $DATABASE_PATH"

# Change to the project directory
cd $PROJECT_PATH

# Change to the database directory and download files
cd $DATABASE_PATH

# Download key frame folder and unzip it into the static/images directory
gdown 1-92UIqmQ5ODeZlSQ61cjFmUdLVZZ_HfV
unzip -q key_frame_folder_reduced.zip -d $PROJECT_PATH/static/images

# Download FAISS annotation
gdown 1-CDUlIAIYAk5L87tXlYFosbUXQQANam8 -O $DATABASE_PATH/index_caption_hashtag_dict_v2.json

# Download CLIP databases
gdown 1EvNEWTNPe8Tk20-Tn0O6BwAgURLJTHZP -O $DATABASE_PATH/merged_index_hnsw_baseline_v0.bin
gdown 1-85d-oCWU39o9d8Ie0c5093fKTp0IpwO -O $DATABASE_PATH/merged_index_hnsw_baseline_v2.bin

# Download Graph database
gdown 1-AotePkVml3iQONPxCZeK-gDjQFI0Asb -O $DATABASE_PATH/graph_data_full.pkl

# Download hashtag embeddings
gdown 1ZRt1-qvJP2CJcWzGykWQVN9JLHBS5XFR -O $DATABASE_PATH/hashtag_embeddings.pkl
gdown 1tZyr1h8yDJO_CXuMn5ounEEdiFKD530d -O $DATABASE_PATH/hashtag_embeddings.bin

# Download encoded frames
gdown 1-KQx8lD7tHJH-RpbLE9gUBA8k_VV5fsI -O $DATABASE_PATH/encoded_frames.pt

echo "All files downloaded and unzipped!"

# Navigate back to the project directory for running the app
cd $PROJECT_PATH

echo "Changed to project directory: $PROJECT_PATH"
