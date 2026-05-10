from pydantic import BaseModel, RootModel, Field
from typing import Optional
from enum import Enum


class Grade(str, Enum):
    sahih     = "Sahih"
    hasan     = "Hasan"
    daif      = "Da'if (Weak)"
    fabricated = "Maudu (Fabricated)"
    unknown   = "Unknown"


class Lang(str, Enum):
    en = "en"
    ar = "ar"


class SearchRequest(BaseModel):
    query: str
    lang: Lang = Lang.en
    grade_filter: str | None = None
    book_filter: str | None = None


class Hadith(BaseModel):
    hadith_id: int
    book: str
    hadith_en_text: str
    hadith_ar_text: str
    chapter_title_ar: str
    chapter_title_en: str
    grade: str = "Unknown"
    raw_grade: str = ""
    reference: str
    in_book_reference: str


class SearchResult(BaseModel):
    hadith: Hadith
    score: float


class SearchResponse(BaseModel):
    number_of_results: int = 0
    results: list[SearchResult]
    response_time_ms: float | None = None


class QrelEntry(BaseModel):
    query: str
    grades: dict[int, int]




class Metrics(BaseModel):
    AP: float
    RR: float
    p_at_20: float = Field(alias="P@20")
    r_at_20: float = Field(alias="R@20")
    f1_at_20: float = Field(alias="F1@20")
    ndcg_at_20: float = Field(alias="nDCG@20")

    model_config = {"populate_by_name": True}


class QueryResult(BaseModel):
    query_text: Optional[str] = Field(None, alias="Query Text")
    metrics: Metrics = Field(alias="Metrics")
    model_config = {"populate_by_name": True}
class QrelsResults(RootModel[dict[str, dict[str, QueryResult]]]):
    pass


InvertedIndex = dict[str, list[tuple[int, int]]]
DocLengths = dict[int, float]
