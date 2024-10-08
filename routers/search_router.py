##############################################
#-------------GET Request Routes--------------
##############################################

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Pass templates location to all views in FastAPI
templates = Jinja2Templates(directory = 'templates')
router = APIRouter()

# Configure logging to output to the notebook
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from tools.search_utils import perform_search

@router.get("/search/{db_idx}", response_class=HTMLResponse)
async def search_by_image(request: Request,
                          db_idx: int):

    results = perform_search(db_idx, request.app)

    logger.info("The retrieval process is completed!!!")
    return templates.TemplateResponse("v0_search_results.html", {
            "request": request,
            "results": results,
            "total_images": len(results),
            "page": 1,
            "total_pages": 1
        })