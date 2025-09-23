from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)  
class Document:
    id: str          
    title: str       
    text: str        
    author: str      
    ts: str 


@dataclass(frozen=True)
class User:
    id: str
    name: str


@dataclass(frozen=True)
class Submission:
    id: str
    user_id: str     
    text: str        
    ts: str          


@dataclass(frozen=True)
class Rule:
    id: str
    kind: str                    
    payload: Dict[str, Any]      
