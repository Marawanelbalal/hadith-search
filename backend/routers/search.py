from fastapi import APIRouter, Depends
import time

from models.schemas import SearchRequest, SearchResponse, SearchResult, Hadith
from scripts.loading import (
    get_english_inverted_index,
    get_arabic_inverted_index,
    get_document_lengths,
    get_english_embeddings,
    get_arabic_embeddings,
    get_hadith_ids,
    get_hadiths_df,
    get_model,
)
from scripts.search import (
    ranked_boolean_retrieval,
    tf_idf,
    bm25,
    bm25_tfidf_hybrid,
    bm25_with_expansion,
    bm25_cross_encoder_rerank,
    final_search_pipeline,
    get_hadith,
    semantic_reranker,
    semantic_search_e5,
    bm25_semantic_rrf
)

router = APIRouter()


def build_results(
    raw: dict[int, float],
    hadiths_df,
    grade_filter: str | None = None,
    book_filter: str | None = None,
    top_k: int = 500,
) -> list[SearchResult]:
    output: list[SearchResult] = []

    for hadith_id, score in raw.items():
        try:
            row = hadiths_df.loc[int(hadith_id)]
        except KeyError:
            continue

        if grade_filter and row.get("Normalized_Grade") != grade_filter:
            continue
        if book_filter and row.get("Book") != book_filter:
            continue

        hadith = Hadith(
            hadith_id=int(hadith_id),
            book=row.get("Book", ""),
            hadith_en_text=row.get("English_Text", ""),
            hadith_ar_text=row.get("Arabic_Text", ""),
            chapter_title_en=row.get("Chapter_Title_English", ""),
            chapter_title_ar=row.get("Chapter_Title_Arabic", ""),
            grade=row.get("Normalized_Grade", "Unknown"),
            raw_grade=row.get("Grade", "Unknown"),
            reference=row.get("Reference", ""),
            in_book_reference=row.get("In-book reference", ""),
        )
        output.append(SearchResult(hadith=hadith, score=float(score)))

    return output[:top_k]


@router.post("/search/boolean", response_model=SearchResponse)
def boolean_search(
    req: SearchRequest,
    english_inverted_index=Depends(get_english_inverted_index),
    arabic_inverted_index=Depends(get_arabic_inverted_index),
    hadiths_df=Depends(get_hadiths_df),
):
    t0 = time.perf_counter()
    idx = english_inverted_index if req.lang.value == "en" else arabic_inverted_index
    raw = ranked_boolean_retrieval(req.query, req.lang.value.upper(), idx)
    results = build_results(raw, hadiths_df, req.grade_filter, req.book_filter)
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResponse(number_of_results=len(results), results=results, response_time_ms=round(elapsed, 2))


@router.post("/search/tfidf", response_model=SearchResponse)
def tfidf_search(
    req: SearchRequest,
    english_inverted_index=Depends(get_english_inverted_index),
    arabic_inverted_index=Depends(get_arabic_inverted_index),
    document_lengths=Depends(get_document_lengths),
    hadiths_df=Depends(get_hadiths_df),
):
    t0 = time.perf_counter()
    idx = english_inverted_index if req.lang.value == "en" else arabic_inverted_index
    raw = tf_idf(req.query, req.lang.value.upper(), idx, document_lengths)
    results = build_results(raw, hadiths_df, req.grade_filter, req.book_filter)
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResponse(number_of_results=len(results), results=results, response_time_ms=round(elapsed, 2))


@router.post("/search/bm25", response_model=SearchResponse)
def bm25_search(
    req: SearchRequest,
    english_inverted_index=Depends(get_english_inverted_index),
    arabic_inverted_index=Depends(get_arabic_inverted_index),
    document_lengths=Depends(get_document_lengths),
    hadiths_df=Depends(get_hadiths_df),
):
    t0 = time.perf_counter()
    idx = english_inverted_index if req.lang.value == "en" else arabic_inverted_index
    raw = bm25(req.query, req.lang.value.upper(), idx, document_lengths)
    results = build_results(raw, hadiths_df, req.grade_filter, req.book_filter)
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResponse(number_of_results=len(results), results=results, response_time_ms=round(elapsed, 2))


@router.post("/search/bm25-tf-idf", response_model=SearchResponse)
def hybrid_search(
    req: SearchRequest,
    english_inverted_index=Depends(get_english_inverted_index),
    arabic_inverted_index=Depends(get_arabic_inverted_index),
    document_lengths=Depends(get_document_lengths),
    hadiths_df=Depends(get_hadiths_df),
):
    t0 = time.perf_counter()
    idx = english_inverted_index if req.lang.value == "en" else arabic_inverted_index
    raw = bm25_tfidf_hybrid(req.query, req.lang.value.upper(), idx, document_lengths)
    results = build_results(raw, hadiths_df, req.grade_filter, req.book_filter)
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResponse(number_of_results=len(results), results=results, response_time_ms=round(elapsed, 2))


@router.post("/search/bm25-prf", response_model=SearchResponse)
def bm25_prf_search(
    req: SearchRequest,
    english_inverted_index=Depends(get_english_inverted_index),
    arabic_inverted_index=Depends(get_arabic_inverted_index),
    document_lengths=Depends(get_document_lengths),
    hadiths_df=Depends(get_hadiths_df),
):
    t0 = time.perf_counter()
    idx = english_inverted_index if req.lang.value == "en" else arabic_inverted_index
    raw = bm25_with_expansion(req.query, req.lang.value.upper(), idx, document_lengths, get_hadith)
    results = build_results(raw, hadiths_df, req.grade_filter, req.book_filter)
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResponse(number_of_results=len(results), results=results, response_time_ms=round(elapsed, 2))


@router.post("/search/semantic-rerank", response_model=SearchResponse)
def semantic_rerank(
    req: SearchRequest,
    english_inverted_index=Depends(get_english_inverted_index),
    arabic_inverted_index=Depends(get_arabic_inverted_index),
    document_lengths=Depends(get_document_lengths),
    english_embeddings=Depends(get_english_embeddings),
    arabic_embeddings=Depends(get_arabic_embeddings),
    hadith_ids=Depends(get_hadith_ids),
    model=Depends(get_model),
    hadiths_df=Depends(get_hadiths_df),
):
    t0 = time.perf_counter()
    lang = req.lang.value
    idx = english_inverted_index if lang == "en" else arabic_inverted_index
    embeddings = english_embeddings if lang == "en" else arabic_embeddings
    bm25_results = bm25(req.query, lang.upper(), idx, document_lengths)
    candidate_ids = list(bm25_results.keys())[:50]
    raw = semantic_reranker(req.query, candidate_ids, model, embeddings, hadith_ids, top_k=10)
    results = build_results(raw, hadiths_df, req.grade_filter, req.book_filter)
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResponse(number_of_results=len(results), results=results, response_time_ms=round(elapsed, 2))


@router.post("/search/cosine-similarity", response_model=SearchResponse)
def cosine_similarity(
    req: SearchRequest,
    english_embeddings=Depends(get_english_embeddings),
    arabic_embeddings=Depends(get_arabic_embeddings),
    hadith_ids=Depends(get_hadith_ids),
    model=Depends(get_model),
    hadiths_df=Depends(get_hadiths_df),
):
    t0 = time.perf_counter()
    lang = req.lang.value
    embeddings = english_embeddings if lang == "en" else arabic_embeddings
    raw = semantic_search_e5(req.query, model, embeddings, hadith_ids, top_k=20)
    results = build_results(raw, hadiths_df, req.grade_filter, req.book_filter)
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResponse(number_of_results=len(results), results=results, response_time_ms=round(elapsed, 2))


@router.post("/search/semantic-rrf", response_model=SearchResponse)
def semantic_rrf(
    req: SearchRequest,
    english_inverted_index=Depends(get_english_inverted_index),
    arabic_inverted_index=Depends(get_arabic_inverted_index),
    document_lengths=Depends(get_document_lengths),
    english_embeddings=Depends(get_english_embeddings),
    arabic_embeddings=Depends(get_arabic_embeddings),
    hadith_ids=Depends(get_hadith_ids),
    model=Depends(get_model),
    hadiths_df=Depends(get_hadiths_df),
):
    t0 = time.perf_counter()
    lang = req.lang.value
    raw = bm25_semantic_rrf(
        req.query, lang.upper(),
        english_inverted_index if lang == "en" else arabic_inverted_index,
        document_lengths,
        english_embeddings if lang == "en" else arabic_embeddings,
        hadith_ids,
        model
    )
    results = build_results(raw, hadiths_df, req.grade_filter, req.book_filter)
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResponse(number_of_results=len(results), results=results, response_time_ms=round(elapsed, 2))


@router.post("/search/final-pipeline", response_model=SearchResponse)
def final_pipeline(
    req: SearchRequest,
    english_inverted_index=Depends(get_english_inverted_index),
    arabic_inverted_index=Depends(get_arabic_inverted_index),
    document_lengths=Depends(get_document_lengths),
    english_embeddings=Depends(get_english_embeddings),
    arabic_embeddings=Depends(get_arabic_embeddings),
    hadith_ids=Depends(get_hadith_ids),
    model=Depends(get_model),
    hadiths_df=Depends(get_hadiths_df),
):
    t0 = time.perf_counter()
    lang = req.lang.value
    embeddings = english_embeddings if lang == "en" else arabic_embeddings
    text_col = "English_Text" if lang == "en" else "Arabic_Text"

    eval_ids = set(map(int, hadith_ids))
    texts_dict = hadiths_df[text_col].dropna().astype(str).to_dict()

    raw = final_search_pipeline(
        query=req.query,
        language=lang.upper(),
        index=english_inverted_index if lang == "en" else arabic_inverted_index,
        doc_lengths=document_lengths,
        embeddings=embeddings,
        hadith_ids=hadith_ids,
        model=model,
        eval_ids=eval_ids,
        texts_dict=texts_dict,
    )
    results = build_results(raw, hadiths_df, req.grade_filter, req.book_filter)
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResponse(number_of_results=len(results), results=results, response_time_ms=round(elapsed, 2))


@router.post("/search/cross-encoder-rerank", response_model=SearchResponse)
def cross_encoder_rerank(
    req: SearchRequest,
    english_inverted_index=Depends(get_english_inverted_index),
    arabic_inverted_index=Depends(get_arabic_inverted_index),
    document_lengths=Depends(get_document_lengths),
    hadiths_df=Depends(get_hadiths_df),
):
    t0 = time.perf_counter()
    lang = req.lang.value
    idx = english_inverted_index if lang == "en" else arabic_inverted_index
    raw = bm25_cross_encoder_rerank(req.query, lang.upper(), idx, document_lengths, hadiths_df)
    results = build_results(raw, hadiths_df, req.grade_filter, req.book_filter)
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResponse(number_of_results=len(results), results=results, response_time_ms=round(elapsed, 2))
