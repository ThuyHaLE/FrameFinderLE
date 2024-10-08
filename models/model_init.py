import torch
import clip

# Configure logging to output to the notebook
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def load_model(model_name="ViT-B/32"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Device: {device}")
    model, preprocess = clip.load(model_name, device=device)
    logger.info(f"The CLIP model ({model_name}) is ready!!!")
    return device, model
