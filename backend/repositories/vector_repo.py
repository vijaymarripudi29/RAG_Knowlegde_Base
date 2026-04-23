from pathlib import Path

import faiss
import numpy as np

from core.config import settings


class VectorRepo:
    def __init__(self):
        self.indices = {}
        self.docs = {}
        self.storage_dir = Path(settings.vector_store.STORAGE_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, user_id, session_id=None):
        namespace = session_id or "default"
        return f"{user_id}__{namespace}"

    def _user_dir(self, user_id, session_id=None):
        safe_user_id = "".join(ch for ch in str(user_id) if ch.isalnum() or ch in ("-", "_"))
        safe_session_id = "".join(ch for ch in str(session_id or "default") if ch.isalnum() or ch in ("-", "_"))
        return self.storage_dir / safe_user_id / safe_session_id

    def _index_path(self, user_id, session_id=None):
        return self._user_dir(user_id, session_id) / "index.bin"

    def _docs_path(self, user_id, session_id=None):
        return self._user_dir(user_id, session_id) / "docs.npy"

    def _new_index(self):
        return faiss.IndexFlatL2(settings.vector_store.FAISS_DIMENSIONS)

    def _load(self, user_id, session_id=None):
        key = self._key(user_id, session_id)
        index_path = self._index_path(user_id, session_id)
        docs_path = self._docs_path(user_id, session_id)

        if index_path.exists() and docs_path.exists():
            self.indices[key] = faiss.read_index(str(index_path))
            self.docs[key] = np.load(str(docs_path), allow_pickle=True).tolist()
            return

        self.indices[key] = self._new_index()
        self.docs[key] = []

    def _save(self, user_id, session_id=None):
        key = self._key(user_id, session_id)
        user_dir = self._user_dir(user_id, session_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.indices[key], str(self._index_path(user_id, session_id)))
        np.save(str(self._docs_path(user_id, session_id)), np.array(self.docs[key], dtype=object))

    def _get_index(self, user_id, session_id=None):
        key = self._key(user_id, session_id)
        if key not in self.indices:
            self._load(user_id, session_id)
        return self.indices[key]

    def add(self, user_id, embedding, text, session_id=None):
        key = self._key(user_id, session_id)
        index = self._get_index(user_id, session_id)
        index.add(np.array([embedding], dtype="float32"))
        self.docs[key].append(text)
        self._save(user_id, session_id)

    def search(self, user_id, embedding, k=settings.vector_store.SEARCH_K, session_id=None):
        key = self._key(user_id, session_id)
        index = self._get_index(user_id, session_id)

        if key not in self.docs or len(self.docs[key]) == 0:
            return []

        result_count = min(k, len(self.docs[key]))
        _, indexes = index.search(np.array([embedding], dtype="float32"), result_count)
        return [self.docs[key][i] for i in indexes[0] if 0 <= i < len(self.docs[key])]

    def replace(self, user_id, embedded_chunks, session_id=None):
        key = self._key(user_id, session_id)
        self.indices[key] = self._new_index()
        self.docs[key] = []

        for embedding, text in embedded_chunks:
            self.indices[key].add(np.array([embedding], dtype="float32"))
            self.docs[key].append(text)

        self._save(user_id, session_id)

    def clear(self, user_id, session_id=None):
        key = self._key(user_id, session_id)
        self.indices[key] = self._new_index()
        self.docs[key] = []
        self._save(user_id, session_id)
