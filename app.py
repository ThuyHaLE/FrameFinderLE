import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any
from models.model_init import load_model
from database.db_init import (
    load_grafa_database,
    load_hashtag_embeddings,
    load_hashtag_embedding_bin,
    load_annotation,
    load_encoded_frames,
    faiss_database_processing,
)

#Creates a FastAPI instance
app = FastAPI()

# Initialize the model and its preprocessing function
device, model = load_model()

# Initialize the database
G, sparse_matrix, node_mapping, reverse_node_mapping = load_grafa_database()
hashtag_embeddings = load_hashtag_embeddings()
hashtag_embedding_index = load_hashtag_embedding_bin()
image_info_dict = load_annotation()
encoded_frames = load_encoded_frames(device)
clipv0_hnsw = faiss_database_processing('CLIP_v0')
clipv2_hnsw = faiss_database_processing('CLIP_v2')

# Initialize the shared database
app.state.device = device
app.state.model = model
app.state.G = G
app.state.sparse_matrix = sparse_matrix
app.state.node_mapping = node_mapping
app.state.reverse_node_mapping = reverse_node_mapping
app.state.hashtag_embeddings = hashtag_embeddings
app.state.hashtag_embedding_index = hashtag_embedding_index
app.state.image_info_dict = image_info_dict
app.state.encoded_frames = encoded_frames
app.state.clipv0_hnsw = clipv0_hnsw
app.state.FEEDBACK_STORE: Dict[str, Any] = {}
app.state.TEMP_FEEDBACK_STORE: Dict[str, Any] = {}

# Include routers
from routers.home_router import router as home_router
from routers.update_results_router import router as update_results_router
from routers.data_router import router as data_router
from routers.search_router import router as search_router
from routers.feedback_router import router as feedback_router
from routers.process_query_router import router as process_query_router

app.include_router(home_router)
app.include_router(update_results_router)
app.include_router(data_router)
app.include_router(search_router)
app.include_router(feedback_router)
app.include_router(process_query_router)

# Mount the content directory to serve static files
app.mount('/static/style',
          StaticFiles(directory=os.path.join(os.getcwd(), 'static/style')),
          name='style')
app.mount('/static/script',
          StaticFiles(directory=os.path.join(os.getcwd(), 'static/script')),
          name='script')
app.mount('/static/images/key_frame_folder_reduced',
          StaticFiles(directory=os.path.join(os.getcwd(), 'static/images/key_frame_folder_reduced')),
          name='key_frame_folder_reduced')

# Run the FastAPI app using Uvicorn on localhost
if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)  # Access via http://0.0.0.0:8000