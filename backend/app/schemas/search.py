from typing import List, Optional, Literal
from pydantic import BaseModel

EntityType = Literal['case','task','message','team','person','file','rfi','ops_plan']

class SearchHit(BaseModel):
    # Display
    title: str
    subtitle: Optional[str] = None
    icon: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # Entity
    entity_type: EntityType
    entity_id: str  # encrypted id of the base entity
    parent_case_id: Optional[str] = None  # encrypted when relevant
    parent_case_number: Optional[str] = None

    # Navigation (path-only, per guidelines)
    primary_path: str
    alt_paths: List[str] = []

    # Ranking
    score: Optional[float] = None

class SearchResponse(BaseModel):
    query: str
    hits: List[SearchHit]
