##############################################
#-------------POST Request Routes--------------
##############################################

from pydantic import BaseModel

from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

# Pass templates location to all views in FastAPI
templates = Jinja2Templates(directory = 'templates')
router = APIRouter()

# Configure logging to output to the notebook
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class FeedbackRequest(BaseModel):
    db_idx: int
    action: str  # This can be 'like', 'dislike', or 'neutral'

@router.post('/update_feedback')
async def update_feedback(request: Request,
                          db_idx: int = Form(...),
                          action: str = Form(...),
                          session_id: str = Form(...)):  # Ensure session_id is expected

    logger.info(f"Received session_id: {session_id}")
    logger.info(f"Received feedback update: db_idx={db_idx}, action={action}")

    # Update temporary feedback store
    TEMP_FEEDBACK_STORE = request.app.state.TEMP_FEEDBACK_STORE
    if session_id not in TEMP_FEEDBACK_STORE:
        TEMP_FEEDBACK_STORE[session_id] = {}
    TEMP_FEEDBACK_STORE[session_id][db_idx] = action

    # Update feedback status
    feedback_status = define_status(action)

    # Return the feedback status and updated temporary store
    return JSONResponse(content={
        'feedbackStatus': feedback_status,
        'tempFeedbackStore': TEMP_FEEDBACK_STORE[session_id]
    })

@router.post('/update_feedback')
async def update_feedback(request: Request,
                          db_idx: int = Form(...),
                          action: str = Form(...),
                          session_id: str = Form(...)):  # Ensure session_id is expected

    logger.info(f"Received session_id: {session_id}")
    logger.info(f"Received feedback update: db_idx={db_idx}, action={action}")

    # Update temporary feedback store
    TEMP_FEEDBACK_STORE = request.app.state.TEMP_FEEDBACK_STORE
    if session_id not in TEMP_FEEDBACK_STORE:
        TEMP_FEEDBACK_STORE[session_id] = {}
    TEMP_FEEDBACK_STORE[session_id][db_idx] = action

    # Update feedback status
    feedback_status = define_status(action)

    # Return the feedback status and updated temporary store
    return JSONResponse(content={
        'feedbackStatus': feedback_status,
        'tempFeedbackStore': TEMP_FEEDBACK_STORE[session_id]
    })

@router.post('/submit_feedback')
async def submit_feedback(request: Request,
                          session_id: str = Form(...)):

    logger.info(f"Submitting feedback for session_id: {session_id}")

    TEMP_FEEDBACK_STORE = request.app.state.TEMP_FEEDBACK_STORE
    FEEDBACK_STORE = request.app.state.FEEDBACK_STORE
    if session_id in TEMP_FEEDBACK_STORE:
        # Transfer temporary feedback to permanent store
        if session_id not in FEEDBACK_STORE:
            FEEDBACK_STORE[session_id] = {}
        FEEDBACK_STORE[session_id].update(TEMP_FEEDBACK_STORE[session_id])
        logger.info(f"Updated feedback store: feedback_store={FEEDBACK_STORE}")

        # Clear temporary feedback for this session
        TEMP_FEEDBACK_STORE[session_id].clear()
        logger.info(f"Cleared temp feedback store: temp_feedback_store={TEMP_FEEDBACK_STORE}")

        # Here you would typically persist the feedback to a database
        # For each db_idx and action in feedback_store[session_id]:
        #     await database.execute("INSERT INTO feedback (db_idx, reaction) VALUES (:db_idx, :action) ON CONFLICT (db_idx) DO UPDATE SET reaction = :action",
        #                            {"db_idx": db_idx, "action": action})

        return JSONResponse(content={
            'message': 'Feedback submitted successfully',
            'submittedFeedback': FEEDBACK_STORE[session_id]
        })
    else:
        logger.info(f"No feedback to submit for session_id: {session_id}")
        return JSONResponse(content={
            'message': 'No feedback to submit'
        })
    
def define_status(action):
    if action == 'like':
        return "You liked this"
    elif action == 'dislike':
        return "You disliked this"
    elif action == 'neutral':
        return "You reset your feedback"
    return "Unknown action"