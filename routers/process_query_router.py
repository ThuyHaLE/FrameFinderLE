##############################################
#-------------POST Request Routes--------------
##############################################

from pydantic import BaseModel

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from tools.hashtags_generating import generate_hashtags

# Pass templates location to all views in FastAPI
templates = Jinja2Templates(directory = 'templates')
router = APIRouter()

# Configure logging to output to the notebook
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Define the request model
class SearchRequest(BaseModel):
    query_text: str = ''

@router.post("/process_query")
async def process_query(request: SearchRequest):
    try:
        # Generate hashtags based on query_text
        query_text = request.query_text or ''
        hashtags = generate_hashtags(query_text)
        logger.info(f"generated_hashtags: {hashtags}")
        return JSONResponse(content={"hashtags": hashtags})
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")