##############################################
#--------------Helper Functions---------------
##############################################

# tools/query_encoding.py
import torch
import clip
import nltk
nltk.download('punkt')

def encode_description(model, device, description):
    """
    Encodes a description into text features using the CLIP model.
    The description is split into sentences, each sentence is tokenized
    and encoded separately. The resulting features are averaged and normalized.

    Args:
        model (CLIP model): The CLIP model used for encoding.
        device (torch.device): The device (CPU or CUDA) to run the model on.
        description (str): The text description to encode.
        
    Returns:
        torch.Tensor: Normalized text features of the description.
    """

    sent_text = nltk.sent_tokenize(description)  # Split the description into sentences

    text_features = torch.zeros((1, 512), dtype=torch.float32).to(device)  # Initialize feature tensor

    for sent in sent_text:
        text_input = clip.tokenize([sent], truncate=True).to(device)  # Tokenize and encode the sentence
        with torch.no_grad():
            text_feature = model.encode_text(text_input)
            text_features += text_feature.sum(dim=0, keepdim=True)  # Sum up features for each sentence

    text_features /= text_features.norm(dim=-1, keepdim=True)  # Normalize the features

    return text_features