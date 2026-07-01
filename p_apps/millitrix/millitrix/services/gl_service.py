
def post_gl(doc):
    # Centralized GL posting (balanced enforcement placeholder)
    return {"status": "ok", "doc": getattr(doc, "name", None)}
