from pydantic import BaseModel
from typing import List, Dict, Optional, Union


class MeterConfig(BaseModel):
    constraints: Optional[List[str]] = None
    max_s: int = 2
    max_w: int = 2
    resolve_optionality: bool = True


class MaxEntFitRequest(BaseModel):
    text: str
    constraints: Optional[List[str]] = None
    max_s: int = 2
    max_w: int = 2
    resolve_optionality: bool = True
    target_scansion: str = "wswswswsws"
    zones: Union[str, int, None] = 3
    regularization: float = 100.0
    syntax: bool = False


class WeightEntry(BaseModel):
    name: str
    weight: float


class MaxEntFitResponse(BaseModel):
    weights: List[WeightEntry]
    elapsed: float
    config: Dict[str, Union[str, int, float, None]]
    accuracy: Optional[float] = None
    num_lines: Optional[int] = None
    num_matched: Optional[int] = None
    log_likelihood: Optional[float] = None


class ReparseRow(BaseModel):
    line_num: int
    line_txt: str
    meter_str: str
    score: float


class MaxEntReparseRequest(BaseModel):
    text: str
    constraints: Optional[List[str]] = None
    max_s: int = 2
    max_w: int = 2
    resolve_optionality: bool = True
    target_scansion: str = "wswswswsws"
    zones: Union[str, int, None] = 3
    regularization: float = 100.0
    syntax: bool = False


class MaxEntReparseResponse(BaseModel):
    rows: List[ReparseRow]
    elapsed: float


class CorpusFile(BaseModel):
    name: str
    path: str
    lang: str
    num_lines: int


class CorpusListResponse(BaseModel):
    files: List[CorpusFile]


class MeterDefaults(BaseModel):
    constraints: List[str]
    max_s: int
    max_w: int
    resolve_optionality: bool


class MeterDefaultsResponse(BaseModel):
    all_constraints: List[str]
    constraint_descriptions: Dict[str, str]
    defaults: MeterDefaults
