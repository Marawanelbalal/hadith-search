from pydantic import BaseModel
from enum import Enum

class Grade(str, Enum):
    sahih = "Sahih"
    hasan = "Hasan"
    daif = "Da'if"
    fabricated = "Fabricated"
    unknown = "Unknown"

class Lang(str, Enum):
    en = "en"
    ar = "ar"

class SearchRequest(BaseModel):
    query : str
    lang : Lang = Lang.en
    grade_filter : str | None = None
    book_filter : str | None = None

class Hadith(BaseModel):
    hadith_id: int
    book: str
    hadith_en_text: str
    hadith_ar_text: str
    chapter_title_ar: str
    chapter_title_en: str
    grade: Grade = Grade.unknown
    reference: str
    in_book_reference: str

class SearchResult(BaseModel):
    hadith: Hadith
    score: float

class SearchResponse(BaseModel):
    number_of_results: int = 0
    results: list[SearchResult]

InvertedIndex = dict[str, list[tuple[int, int]]]
DocLengths = dict[int, float]