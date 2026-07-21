from sentence_transformers import SentenceTransformer

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def get_embedding(text):
    model = _get_model()
    return model.encode(text.replace(chr(10), ' ')).tolist()
