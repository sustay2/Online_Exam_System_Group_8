from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI(title="Agile CI Demo", version="0.1.0")


class Item(BaseModel):
    id: int
    title: str
    done: bool = False


_db: Dict[int, Item] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/items", status_code=201)
def create_item(item: Item):
    if item.id in _db:
        raise HTTPException(status_code=409, detail="Item exists")
    _db[item.id] = item
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id not in _db:
        raise HTTPException(status_code=404, detail="Not found")
    return _db[item_id]


@app.patch("/items/{item_id}/done")
def mark_done(item_id: int):
    if item_id not in _db:
        raise HTTPException(status_code=404, detail="Not found")
    item = _db[item_id]
    item.done = True
    _db[item_id] = item
    return item
