# Hadith Search Engine

A full-stack hadith search engine supporting both English and Arabic queries with multiple ranking algorithms.

## Phase 1: Data Preprocessing

The preprocessing pipeline prepares raw hadith text for efficient retrieval:

### English Pipeline
- **Tokenization**: NLTK `word_tokenize`
- **POS Tagging**: NLTK `pos_tag`
- **Lemmatization**: NLTK `WordNetLemmatizer` with POS-aware lemmatization
- **Stopword Removal**: NLTK English stopwords + custom hadith-specific terms (e.g., "narrate", "authority", "hadith")

### Arabic Pipeline
- **Normalization**: PyArabic for text normalization (alef, teh marbuta, hamza, tatweel removal)
- **Tokenization**: CAMeL Tools `simple_word_tokenize`
- **Morphological Disambiguation**: CAMeL Tools `calima-msa-r13` MLE disambiguator
- **Lemmatization**: Extracted from disambiguation analysis
- **POS-based Filtering**: Removed prepositions, conjunctions, particles, and punctuation

## Phase 2: Index Building & Search Implementation

### Inverted Index Building
The BM25-based algorithms use an inverted index for efficient term-based retrieval:

1. **Build Inverted Index**: Scans preprocessed hadith collection, computes document frequencies and term frequencies
2. **Document Length Storage**: Stores normalized document lengths for BM25's length normalization
3. **Language-specific Indices**: Separate indices for English and Arabic processed texts

### Dense Embeddings
Dense retrieval uses transformer-based embeddings:

1. **Model**: `intfloat/multilingual-e5-large` - Single model handles both English and Arabic
2. **Encoding**: Generates 1024-dimensional embeddings for each hadith (English and Arabic texts)
3. **Normalization**: L2-normalized embeddings for efficient cosine similarity computation

### Search Functions Available

| Algorithm | Description |
|-----------|-------------|
| **Term Overlap** | Exact matches ranked by term frequency |
| **TF-IDF** | Classic term frequency-inverse document frequency ranking |
| **BM25** | Okapi BM25 with optimized k1 and b parameters |
| **BM25 + TF-IDF (Hybrid)** | Combines BM25 and TF-IDF scores with weighted fusion |
| **BM25 + PRF** | BM25 with pseudo-relevance feedback (query expansion) |
| **Cosine Similarity** | Dense retrieval using vector embeddings and cosine similarity |
| **Semantic Rerank** | Cosine similarity results reranked by cross-encoder |
| **Semantic RRF** | Reciprocal Rank Fusion combining sparse (BM25) and dense (cosine) results |
| **Cross-Encoder Rerank** | Direct reranking of BM25 results using cross-encoder model |
| **Final Pipeline** | Full pipeline: BM25 → Semantic Reranking → Cross Encoding |

### Search Architecture
- **Sparse Retrieval**: BM25, TF-IDF, Term Overlap - Fast, interpretable, language-independent
- **Dense Retrieval**: Cosine Similarity using multilingual-e5-large embeddings
- **Reranking**: jinaai/jina-reranker-v2-base-multilingual for precision improvement
- **Fusion**: Reciprocal Rank Fusion (RRF) for combining multiple retrieval methods

## External Dependencies

Beyond pip-installed libraries, this project requires:

### NLTK Data
```python
import nltk
nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')
```

### HuggingFace Models (auto-downloaded)
- `intfloat/multilingual-e5-large` - Sentence transformer for dense retrieval

### CAMeL Tools Models (auto-downloaded)
- `calima-msa-r13` - Arabic morphological disambiguator (loaded via `camel_tools.disambig.mle.MLEDisambiguator.pretrained("calima-msa-r13")`)

### External APIs
- **Jina AI Reranker API** - Requires a Jina AI API key (not a downloaded model). Set via environment variable `JINA_API_KEY`

## Running the Project

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` by default.

## Project Structure

```
hadith-search/
├── backend/
│   ├── data/                 # Preprocessed data (embeddings, indices, DB)
│   ├── routers/              # FastAPI endpoints
│   ├── scripts/              # Data processing & indexing scripts
│   └── main.py               # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── api/              # API client
│   │   └── i18n/             # Internationalization
│   └── package.json
└── requirements.txt
```

## Available Scripts

### Data Processing
- `backend/scripts/build_embeddings.py` - Generate dense embeddings (requires CUDA)
- `backend/scripts/build_inverted_index.py` - Build BM25 inverted index
- `backend/scripts/preprocess.py` - Preprocess hadith text

## Tech Stack

- **Backend**: FastAPI, SQLite, NLTK, CAMeL Tools, Sentence Transformers
- **Frontend**: React, TypeScript, Tailwind CSS, Vite
- **Retrieval**: BM25, BM25+PRF, Dense retrieval (multilingual-e5-large), Hybrid
