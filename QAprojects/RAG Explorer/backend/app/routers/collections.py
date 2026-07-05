from fastapi import APIRouter, HTTPException

from .. import state, vectorstore
from ..schemas import CollectionInfo, CollectionsResponse
from ..vectorstore import VectorStoreError

router = APIRouter(prefix="/api/collections", tags=["collections"])


@router.get("", response_model=CollectionsResponse)
def list_collections():
    try:
        active = state.get_active()
        names = vectorstore.list_collections()
        meta = state.all_meta()
        infos = []
        for name in names:
            m = meta.get(name, {"label": name})
            infos.append(
                CollectionInfo(
                    name=name,
                    label=m.get("label", name),
                    chunk_count=vectorstore.collection_count(name),
                    is_active=(name == active),
                )
            )
        return CollectionsResponse(collections=infos, active=active)
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/{name}/activate", response_model=CollectionsResponse)
def activate_collection(name: str):
    try:
        if name not in vectorstore.list_collections():
            raise HTTPException(status_code=404, detail=f"Collection '{name}' not found.")
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    state.set_active(name)
    return list_collections()


@router.delete("/{name}")
def delete_collection(name: str):
    try:
        vectorstore.delete_collection(name)
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if state.get_active() == name:
        state.set_active("default")
    return {"deleted": name}
