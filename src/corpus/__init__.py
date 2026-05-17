"""Document corpus package.

The env var below MUST be set before any chromadb / google.protobuf import.
Because `src.corpus` is the parent package of `src.corpus.config` and
`src.corpus.query` — every module that touches chromadb imports through
here — setting it in __init__.py guarantees it runs first, regardless of
which submodule Streamlit Cloud loads first.

This is a workaround for a chromadb / protobuf version mismatch on
Streamlit Cloud's wheel cache (TypeError: 'Descriptors cannot be created
directly...'). Pure-Python parsing is slower but invariant to the
installed protobuf binary version.
"""

import os
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
