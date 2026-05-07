from fastapi import APIRouter
from models.schemas import SearchRequest, SearchResponse, SearchResult, Hadith, Grade
from scripts.search import bm25, bm25_with_expansion, tf_idf, ranked_boolean_retrieval, bm25_tfidf_hybrid
from dependencies import get_hadiths_df

router = APIRouter(prefix="/search", tags=["search"])

def build_results(scores: dict[int, float], top_k: int) -> list[SearchResult]:
    df = get_hadiths_df()
    results = []
    for hadith_id in list(scores.keys())[:top_k]:
        try:
            row = df.loc[hadith_id]
        except KeyError:
            continue
        results.append(SearchResult(
            score=scores[hadith_id],
            hadith=Hadith(
                hadith_id=hadith_id,
                book=row["Book"],
                hadith_en_text=row["English_Text"],
                hadith_ar_text=row["Arabic_Text"],
                chapter_title_ar=row["Chapter_Arabic"],
                chapter_title_en=row["Chapter_English"],
                grade=row.get("Grade", Grade.unknown),
                reference=row["Reference"],
                in_book_reference=row["In_Book_Reference"],
            )
        ))
    return results

@router.post("/bm25")
def search_bm25(req: SearchRequest) -> SearchResponse:
    scores = bm25(req.query, req.lang.value.upper())
    results = build_results(scores, req.top_k)
    return SearchResponse(results=results, number_of_results=len(results))

@router.post("/bm25-expanded")
def search_bm25_expanded(req: SearchRequest) -> SearchResponse:
    scores = bm25_with_expansion(req.query, req.lang.value.upper())
    results = build_results(scores, req.top_k)
    return SearchResponse(results=results, number_of_results=len(results))

@router.post("/tfidf")
def search_tfidf(req: SearchRequest) -> SearchResponse:
    scores = tf_idf(req.query, req.lang.value.upper())
    results = build_results(scores, req.top_k)
    return SearchResponse(results=results, number_of_results=len(results))

@router.post("/ranked-boolean")
def search_ranked_boolean(req: SearchRequest) -> SearchResponse:    
    scores = ranked_boolean_retrieval(req.query, req.lang.value.upper())
    results = build_results(scores, req.top_k)
    return SearchResponse(results=results, number_of_results=len(results))

@router.post("/bm25-tfidf-hybrid")
def search_bm25_tfidf_hybrid(req: SearchRequest) -> SearchResponse:
    scores = bm25_tfidf_hybrid(req.query, req.lang.value.upper())
    results = build_results(scores, req.top_k)
    return SearchResponse(results=results, number_of_results=len(results))