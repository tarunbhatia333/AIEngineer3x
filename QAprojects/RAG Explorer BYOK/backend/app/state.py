from . import config

# Simple in-process state: which collection is "active" for querying,
# and human-readable labels + source filenames per collection.
_active_collection = config.DEFAULT_COLLECTION
_collection_meta: dict[str, dict] = {}


def set_active(name: str):
    global _active_collection
    _active_collection = name


def get_active() -> str:
    return _active_collection


def set_meta(name: str, label: str, source: str):
    _collection_meta[name] = {"label": label, "source": source}


def get_meta(name: str) -> dict:
    return _collection_meta.get(name, {"label": name, "source": ""})


def all_meta() -> dict[str, dict]:
    return dict(_collection_meta)
