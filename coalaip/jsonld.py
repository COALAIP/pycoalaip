import pyld


jsonld = pyld.jsonld

# Use a custom document loader to cache context requests
# TODO: save coalaip and schema.org's context as .json files and load
#       them here to avoid requesting them
_default_document_loader = jsonld.get_document_loader()
_CONTEXTS = {}


def _custom_document_loader(url):
    if url in _CONTEXTS:
        return _CONTEXTS[url]

    requested_ctx = _default_document_loader(url)
    _CONTEXTS[url] = requested_ctx
    return requested_ctx


jsonld.set_document_loader(_custom_document_loader)
