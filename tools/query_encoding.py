# tools/query_encoding.py

import torch
import model_state

def _chunks(lst, chunk_size):
    """Split a list into smaller lists, each with a maximum of chunk_size elements."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def encode_texts(texts, batch_size=32, truncate_dim=None, chunk_size=500, sort_by_length=True, show_progress=False):
    """Encode a list of texts using the jina-clip-v2 model.
    :param texts: List of strings to be encoded.
    :param batch_size: Number of texts to process in a single batch.
    :param truncate_dim: Dimension to truncate the text embeddings to. Must match the dimension used when encoding images.
    :param chunk_size: Number of texts to process in a single chunk. This is useful for large datasets to avoid memory issues.
    :param sort_by_length: Whether to sort texts by length before encoding. This can improve efficiency for variable-length texts.
    :param show_progress: Whether to display a progress bar during encoding. Useful for long-running processes.
    :return: A torch.Tensor of shape (N, dim) containing the normalized embeddings, in the same order as the input texts.
    """

    n = len(texts)
    if sort_by_length:
        order = sorted(range(n), key=lambda i: len(texts[i]))
    else:
        order = list(range(n))
    sorted_texts = [texts[i] for i in order]

    all_features = []
    for chunk in _chunks(sorted_texts, chunk_size):
        with torch.no_grad():
            embeddings = model_state.MODEL.encode_text(chunk, 
                                        batch_size=batch_size, 
                                        truncate_dim=truncate_dim)
        feats = torch.tensor(embeddings, dtype=torch.float32)
        feats = feats / feats.norm(dim=-1, keepdim=True)
        all_features.append(feats.cpu())

    all_features = torch.cat(all_features, dim=0)
    inverse_order = torch.argsort(torch.tensor(order))
    all_features = all_features[inverse_order]
    return all_features