# CrewAI Content Production System — Tools Deep Dive

This document explains every tool implementation in the backend `tools/` folder: what each tool does, the logic and algorithms behind it, inputs/outputs, configuration, operational notes, and testing suggestions.

Files covered:
- `backend/tools/grammar_tool.py`
- `backend/tools/tavily_tool.py`
- `backend/tools/seo_tool.py`
- `backend/tools/plagiarism_tool.py`

Use this as a single reference when extending tools, tuning thresholds, or integrating tools with agents and the Quality Gate.

---

## 1) Grammar Tool (LanguageTool integration)

Location: `backend/tools/grammar_tool.py`

Purpose
- Provide programmatic grammar, spelling, and style checks using LanguageTool.
- Offer both a plain Python wrapper (`GrammarCheckTool`) for programmatic use (Quality Gate) and a `CrewAI` agent-compatible tool (`CrewAIGrammarCheckTool`) that returns a human-readable report.

How it works (logic)
- Sends a POST request to the LanguageTool API endpoint (`LANGUAGETOOL_API_URL` or the public `https://api.languagetool.org/v2/check`) with `text` and `language` parameters.
- Receives a JSON response containing `matches` — each match includes rule metadata, suggested replacements, offsets, and context.
- Converts each match into a `GrammarMatch` dataclass with fields: `message`, `short_message`, `offset`, `length`, `matched_text`, `replacements`, `rule_id`, `rule_description`, `category`.
- Returns `GrammarCheckResponse` containing the original text, language, list of matches, and `is_valid` flag (true if no matches).

Inputs
- `text` (str) — full article or fragment to be checked.
- `language` (str) — language code (default `en-US`).

Outputs
- `GrammarCheckResponse` (programmatic): contains `matches` and `is_valid` boolean.
- Human readable string (via `CrewAIGrammarCheckTool._run`) summarizing issues and suggestions.

Error handling & edge cases
- Returns `is_valid=True` for empty input (no work to do).
- Network or API errors raise exceptions, logged via Loguru. The CrewAI wrapper returns a friendly error string on exceptions.

Configuration
- `LANGUAGETOOL_API_URL` environment variable to point to an internal LanguageTool server or public API.
- Timeout: requests use a 10s timeout.

Performance & cost
- Each check triggers a network call; latency depends on the LanguageTool provider. For high throughput, consider hosting a local LanguageTool server.

Integration with Quality Gate
- Quality Gate counts matches and treats the number of matches as grammar errors; tuning `QualityGate.max_grammar_errors` is used to adjust strictness.

Testing recommendations
- Unit test by mocking `requests.post` to return controlled `matches` payloads.
- Integration test against a local LanguageTool instance or a recorded HTTP response (VCR/cassette).

Example usages
- Programmatic: `GrammarCheckTool().check(article_text)`
- Agent tool: `CrewAIGrammarCheckTool()` invoked in the Editor Agent to get a readable report.

---

## 2) Tavily Search Tool

Location: `backend/tools/tavily_tool.py`

Purpose
- Provide clean, structured web search results and an optional AI-generated answer using the Tavily Search API tailored for agent consumption.

How it works (logic)
- Uses `tavily.TavilyClient` with `TAVILY_API_KEY` to send a query; requests include `max_results`, `include_answer`, and `search_depth` (set to `advanced` for deeper results).
- Parses the raw response into `SearchResult` dataclasses with `title`, `url`, `content`, and `score` and into `SearchResponse` containing `query`, `results`, and `answer`.

Inputs
- `query` (str) — search query
- `max_results` (int, default 5)
- `include_answer` (bool, default True) — whether to include Tavily's AI summary

Outputs
- `SearchResponse` with typed `SearchResult` list and optional `answer` (string) that provides a concise summary.

Error handling & edge cases
- Raises `EnvironmentError` if `TAVILY_API_KEY` is not set.
- Exceptions from the Tavily client are logged and bubbled up.

Integration considerations
- Tavily returns cleaned and summarized content — ideal for the Researcher Agent to avoid raw HTML scraping and parsing.
- Use `include_answer` when you want Tavily to provide a short summary; otherwise, you can prefer agent-generated summaries from multiple results.

Testing recommendations
- Unit test by mocking `TavilyClient.search()` to return structured results.
- For integration tests, use a test Tavily API key or recorded responses.

Performance & cost
- Tavily usage is subject to API rate limits and billing. Cache search results for identical queries to reduce cost and latency.

Example usage
- `tool = TavilySearchTool(); res = tool.search('renewable energy trends'); res.results[0].title`

---

## 3) SEO Keyword Analyzer

Location: `backend/tools/seo_tool.py`

Purpose
- Analyze an article for target keyword coverage, density, and placement, and compute an overall SEO score (0–100). Provide actionable suggestions.

How it works (logic)
- Cleans the article text to remove basic markdown and punctuation artifacts.
- Identifies `headline` (Markdown H1 `# ` or first non-empty line), `introduction` (first paragraph after headline), and `subheadings` (lines starting with `##`, `###`, `####`).
- Computes cleaned word count and for each keyword:
  - Counts occurrences using word-boundary regex (case-insensitive).
  - Computes density = (count / word_count) * 100.
  - Checks presence in headline, introduction, and subheadings.
  - Assigns a `status` (`not_found`, `low`, `optimal`, `stuffed`) based on density ranges:
    - <0.5% → `low`
    - 0.5%–1.0% → `low` (ramped score)
    - 1.0%–2.5% → `optimal`
    - >2.5% → `stuffed` (penalized; heavy >5% reduced to 0)
- Computes a per-keyword score composed of:
  - Density score (40%), headline presence (20%), introduction presence (20%), subheadings presence (20%).
- Averages per-keyword scores into an overall SEO score. Penalizes very short articles (<300 words) by reducing the final score.

Inputs
- `text` (str) — article
- `keywords` (List[str]) — target keywords to check

Outputs
- `SEOResponse` with `score` (float), `keyword_metrics` mapping each keyword to `KeywordMetrics` (count, density, placements, status), `word_count`, and `suggestions` (list).
- `CrewAISEOTool` returns a detailed human-readable report for agents.

Error handling & edge cases
- If `text` or `keywords` are empty, returns score 0 and suggestion indicating empty inputs.
- Word counting strips basic markdown characters; more advanced markdown should be cleaned before analysis if needed.

Configuration & tuning
- Density thresholds and score weights are hardcoded; adjust these constants if different SEO strategy is desired (e.g., more weight to headline placement).

Integration with Quality Gate
- Quality Gate uses the `seo_score` and compares to `min_seo_score` threshold (default 70.0) — tune this threshold to match content goals.

Testing recommendations
- Unit tests for density calculations, placement detection, and scoring with controlled text and keywords.
- Edge-case tests: headline-only text, short texts, repeated keywords (stuffing scenarios).

Usage example
- `SEOKeywordAnalyzer().analyze(article_text, ['ai in healthcare','diagnostics'])`

---

## 4) Plagiarism Detector (Semantic)

Location: `backend/tools/plagiarism_tool.py`

Purpose
- Detect semantic duplication or paraphrase-level plagiarism by comparing sentence embeddings against reference documents using SentenceTransformers.

How it works (logic)
- Splits the article and reference documents into sentences (regex-based split), filters out short fragments (<15 chars).
- Loads (lazily) a SentenceTransformer model (`all-MiniLM-L6-v2`) cached as a class attribute to avoid repeated loads.
- Encodes input sentences and all reference sentences into embeddings.
- Computes cosine similarity matrix between input and reference sentence embeddings using `sentence_transformers.util.cos_sim`.
- For each input sentence, finds the best matching reference sentence and flags it as a match if similarity >= `threshold` (default 0.80).
- Computes plagiarism percentage = (matched_input_sentences / total_input_sentences) * 100 and rounds to 1 decimal place.
- Returns `PlagiarismResponse` containing `score` (percentage), `matches` (list of `PlagiarizedSentence`), `is_safe` (true if < 15% by default), and the matching `threshold`.

Inputs
- `text` (str) — article to check
- `reference_docs` (List[str]) — texts to check against (could be database excerpts, competitor articles, or previously published content)

Outputs
- `PlagiarismResponse` with `score` (float), list of matched sentences with similarity scores and source index, and `is_safe` boolean.

Error handling & edge cases
- If no reference docs or no text, returns score 0 and `is_safe=True`.
- Raises exceptions on model load errors; logs helpful messages to indicate missing `sentence_transformers` install.

Performance & scaling
- Encoding all sentences can be memory- and CPU-intensive for large corpora. Strategies:
  - Use smaller embedding models (already uses a compact `all-MiniLM-L6-v2`).
  - Batch encoding and use GPU where available.
  - Pre-index reference document sentence embeddings in a vector DB (e.g., Chroma, LanceDB) and perform approximate nearest neighbors (ANN) queries instead of encode+cos_sim every run.

Thresholds & tuning
- Default similarity threshold = 0.80 (80%). This is conservative for paraphrase-level detection; lower thresholds may produce more matches (higher recall), higher thresholds increase precision.
- Quality Gate treats `< 15%` as safe by default; adjust `QualityGate.max_plagiarism_pct` to change tolerance.

Testing recommendations
- Unit test with a few short texts and reference docs where expected matches are known.
- Integration test using a small reference corpus and verifying that near-duplicate sentences are detected.

Integration notes
- For production, store precomputed embeddings for reference docs in a vector DB and use ANN search (faiss, hnswlib, or a managed service) to scale.
- Consider chunking reference docs and documents into overlapping windows to improve recall for slightly rephrased content.

Usage example
- `PlagiarismDetector().check(article_text, [doc1_text, doc2_text])`

---

## Common Integration Patterns (how agents use tools)

- Research flow: `TavilySearchTool.search()` → produce `SearchResponse.results` → researcher synthesizes into structured research summary.
- Draft editing: `CrewAIGrammarCheckTool` invoked by Editor Agent for human-readable feedback; `GrammarCheckTool` invoked by Quality Gate for programmatic counts.
- SEO tuning: Editor or SEO Agent calls `CrewAISEOTool` for suggestions; Quality Gate calls `SEOKeywordAnalyzer` for numeric `seo_score` used in pass/fail.
- Final verification: Fact Checker uses `TavilySearchTool` + `PlagiarismDetector` to confirm claims and detect duplicates.

## Practical recommendations & next steps

- Host a local LanguageTool server if you run many grammar checks (reduces latency and rate-limit risk).
- Persist reference document embeddings in a vector DB for scalable plagiarism detection.
- Add caching for Tavily queries (query → SearchResponse) to save cost and speed up repeated topics.
- Expose tool-level metrics (counts, error rates, latencies) to monitor reliability and tune thresholds.

## Tests & CI suggestions

- Add unit tests mocking external HTTP calls (`requests.post` for LanguageTool, `TavilyClient.search`) and model calls (mock SentenceTransformer encode to return deterministic embeddings).
- Add a lightweight integration test that runs `SEOKeywordAnalyzer` and `GrammarCheckTool` with fixed inputs.

---

If you want, I can:
- Generate a short cheatsheet file with example invocation snippets for each tool.
- Add unit tests (mocks) for the tools and wire them into CI.
- Scaffold a caching layer or a simple SQLite-backed vector store for reference embeddings.
