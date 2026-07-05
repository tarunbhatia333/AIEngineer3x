from fastapi import APIRouter, Depends, HTTPException

from .. import state, vectorstore
from ..keys import ApiKeys, get_api_keys
from ..schemas import CollectionInfo, CollectionsResponse
from ..vectorstore import VectorStoreError

router = APIRouter(prefix="/api/collections", tags=["collections"])


@router.get("", response_model=CollectionsResponse)
def list_collections(keys: ApiKeys = Depends(get_api_keys)):
    try:
        active = state.get_active()
        names = vectorstore.list_collections(api_key=keys.pinecone)
        meta = state.all_meta()
        infos = []
        for name in names:
            m = meta.get(name, {"label": name})
            infos.append(
                CollectionInfo(
                    name=name,
                    label=m.get("label", name),
                    chunk_count=vectorstore.collection_count(name, api_key=keys.pinecone),
                    is_active=(name == active),
                )
            )
        return CollectionsResponse(collections=infos, active=active)
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/{name}/activate", response_model=CollectionsResponse)
def activate_collection(name: str, keys: ApiKeys = Depends(get_api_keys)):
    try:
        if name not in vectorstore.list_collections(api_key=keys.pinecone):
            raise HTTPException(status_code=404, detail=f"Collection '{name}' not found.")
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    state.set_active(name)
    return list_collections(keys=keys)


@router.delete("/{name}")
def delete_collection(name: str, keys: ApiKeys = Depends(get_api_keys)):
    try:
        vectorstore.delete_collection(name, api_key=keys.pinecone)
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if state.get_active() == name:
        state.set_active("default")
    return {"deleted": name}
