from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from tools.immediate_refining import immediate_refining
from tools.aggregated_refining import aggregated_refining
from tools.results_display import display_option_results
from tools.utils import remove_first_n_elements

from tools.search_utils import cached_results, paginate_results

# Pass templates location to all views in FastAPI
templates = Jinja2Templates(directory = 'templates')
router = APIRouter()

# Configure logging to output to the notebook
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

##############################################
#-------------GET Request Routes--------------
##############################################

@router.get("/", 
            response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/home")

@router.get("/home", response_class=HTMLResponse, 
            operation_id="get_home_page")
async def get_home(request: Request):
    return templates.TemplateResponse('home.html', 
                                      {"request": request})

##############################################
#-------------POST Request Routes--------------
##############################################

@router.post("/home", response_class=HTMLResponse, operation_id="post_home_page")
async def post_home(request: Request,
                    query_text: str = Form(''),
                    hiddenHashtags: str = Form(''),
                    database_name: str = Form("CLIP_v2"),
                    k: int = Form(100),
                    page: int = Form(1),
                    display_option: str = Form('sort_by_frame_index'),
                    images_per_page: int = Form(50),
                    session_id: str = Form(None),
                    refine_status: bool = Form(False),
                    ):

    device = request.app.state.device
    image_info_dict = request.app.state.image_info_dict
    encoded_frames = request.app.state.encoded_frames
    clipv0_hnsw = request.app.state.clipv0_hnsw
    FEEDBACK_STORE = request.app.state.FEEDBACK_STORE

    logger.info(f"Submitting feedback for session_id: {session_id}")
    results, hiddenInitialDBIdx, hiddenInitialDBScore = cached_results(query_text, hiddenHashtags,
                                                                       database_name, k, display_option,
                                                                       request.app)
    logger.info(f"hiddenInitialDBIdx: {hiddenInitialDBIdx}")

    if session_id in FEEDBACK_STORE:
      feedback_status = FEEDBACK_STORE[session_id]
    else:
      feedback_status = {}

    if refine_status == False and feedback_status:
      logger.info(f"Received feedback: {feedback_status}")
      refined_DBScore, refined_DBIdx = immediate_refining(hiddenInitialDBIdx, hiddenInitialDBScore,
                                                          feedback_status, encoded_frames,)
      results = display_option_results(display_option,
                                      refined_DBScore, refined_DBIdx,
                                      image_info_dict)
      logger.info(f"hiddenRefinedDBIdx: {refined_DBIdx}")

    else:
      logger.info(f"Received feedback: {feedback_status}")
      logger.info(f"Refine status: {refine_status}")
      aggregated_DBScore, aggregated_DBIdx = aggregated_refining(hiddenInitialDBIdx, hiddenInitialDBScore,
                                                                  feedback_status, encoded_frames, clipv0_hnsw, device,
                                                                  exploration_ratio=0.2, original_weight=0.7,
                                                                  decay_factor=0.9, window_size=50, time_weight_ratio=0.5,)
      results = display_option_results(display_option,
                                      aggregated_DBScore, aggregated_DBIdx,
                                      image_info_dict)
      logger.info(f"hiddenAggreatedDBIdx: {aggregated_DBIdx}")

    #save space
    if len(FEEDBACK_STORE) >= 100:
      FEEDBACK_STORE = remove_first_n_elements(FEEDBACK_STORE, n=50)

    # Paginate results
    paginated_results, total_images, total_pages = paginate_results(results, page, images_per_page)

    return templates.TemplateResponse('show_results.html',
    {
        'request': request,
        'total_images': total_images,
        'query_text': query_text,
        'hiddenHashtags': hiddenHashtags,
        'database_name': database_name,
        'display_option': display_option,
        'k': k,
        'paginated_results': paginated_results,
        'page': page,
        'images_per_page': images_per_page,
        'total_pages': total_pages})