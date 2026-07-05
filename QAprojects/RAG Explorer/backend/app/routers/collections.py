from fastapi import APIRouter, HTTPException

from .. import state, vectorstore
from ..schemas import CollectionInfo, CollectionsResponse

router = APIRouter(prefix="/api/collections", tags=["collections"])


@router.get("", response_model=CollectionsResponse)
def list_collections():
    active = state.get_active()
    names = vectorstore.list_collections()
    meta = state.all_meta()
    infos = []
    for name in names:
        collection = vectorstore.get_collection(name)
        m = meta.get(name, {"label": name})
        infos.append(
            CollectionInfo(
                name=name,
                label=m.get("label", name),
                chunk_count=collection.count(),
                is_active=(name == active),
            )
        )
    return CollectionsResponse(collections=infos, active=active)


@router.post("/{name}/activate", response_model=CollectionsResponse)
def activate_collection(name: str):
    if name not in vectorstore.list_collections():
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found.")
    state.set_active(name)
    return list_collections()


@router.delete("/{name}")
def delete_collection(name: str):
    try:
        vectorstore.get_client().delete_collection(name=name)
    except Exception:
        pass
    if state.get_active() == name:
        state.set_active("default")
    return {"deleted": name}
