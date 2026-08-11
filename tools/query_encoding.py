##############################################
#--------------Helper Functions---------------
##############################################

# tools/query_encoding.py
import torch

def _chunks(lst, chunk_size):
    """Chia lst thanh cac list con, moi list toi da chunk_size phan tu."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def encode_texts(
        model,
        texts, 
        batch_size=32, 
        truncate_dim=None, 
        chunk_size=500, 
        sort_by_length=True, 
        show_progress=False):
    """
    Encode danh sach text (query ngan, mo ta nhieu cau...) bang jina-clip-v2.
    :param truncate_dim: PHAI KHOP voi truncate_dim da dung khi encode anh!
    :return: torch.Tensor (N, dim) da normalize, dung thu tu voi `texts` dau vao
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
            embeddings = model.encode_text(chunk, 
                                           batch_size=batch_size, 
                                           truncate_dim=truncate_dim)
        feats = torch.tensor(embeddings, dtype=torch.float32)
        feats = feats / feats.norm(dim=-1, keepdim=True)
        all_features.append(feats.cpu())

    all_features = torch.cat(all_features, dim=0)
    inverse_order = torch.argsort(torch.tensor(order))
    all_features = all_features[inverse_order]
    return all_features