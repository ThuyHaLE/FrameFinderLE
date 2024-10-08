##############################################
#-------------GET Request Routes--------------
##############################################

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Optional

from tools.search_utils import cached_get_keyframes

# Pass templates location to all views in FastAPI
templates = Jinja2Templates(directory = 'templates')
router = APIRouter()

# Configure logging to output to the notebook
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@router.get("/data", response_class=HTMLResponse)
async def data_page(request: Request,
                    page: int = 1,
                    video_ID: Optional[str] = 'L01_V001',
                    timestamp: Optional[str] = ''):

    logger.info(f"Received video_ID: {video_ID}")
    logger.info(f"Received timestamp: {timestamp}")
    per_page = 50
    keyframes, total_count = cached_get_keyframes(page, 
                                                  per_page, 
                                                  video_ID, 
                                                  timestamp)
    total_pages = (total_count + per_page - 1) // per_page

    return templates.TemplateResponse('data.html', {
        "request": request,
        "keyframes": keyframes,
        "current_page": page,
        "total_pages": total_pages,
        "video_ID": video_ID,
        "timestamp": timestamp
    })