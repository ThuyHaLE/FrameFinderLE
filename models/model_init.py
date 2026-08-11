import torch
import clip
from transformers import AutoModel

# Configure logging to output to the notebook
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def load_model(model_name='jinaai/jina-clip-v2'):

    # Load model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Device: {device}")

    model = AutoModel.from_pretrained(
        model_name,
        trust_remote_code=True,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        low_cpu_mem_usage=False,
    )
    model = model.to(device)
    model.eval()
    logger.info(f"The CLIP model ({model_name}) is ready!!!")

    return device, model