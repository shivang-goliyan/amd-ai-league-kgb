# Match 3: grounded multi-format document QA

The native Radeon GPU evaluation passed all ten public sample questions, including exact citation sets. CPU behavioral tests and the container build pass. Submitted for grading; mandatory-container/Instinct verification and private results remain pending; see [validation details](../../VALIDATION.md).

## Grader contract

The container retains a single model/index server. Its client accepts both invocations:

```sh
python3 /app/app.py --index /app/corpus
python3 /app/app.py --corpus /app/corpus --query-id query_01 --query 'Question?'
```

A query atomically writes `/app/output/query_01_output.json` with both `answer` and `citations`, including for refusals. No model is loaded inside the client process.

## Pipeline

1. Parse the corpus once: PDF text, DOCX paragraphs and tables in document order, every XLSX sheet, CSV rows with headers, plain-text logs/source, and images read by the resident vision model.
2. Skip encrypted/unreadable files and unsupported formats independently. Exclude explicitly withdrawn revisions. Never execute ingested source code or follow file symlinks outside the corpus.
3. Retain all text in the index, with overlapping passages instead of truncating long logs. Lexical retrieval preserves identifiers and expands rare identifiers for a second retrieval hop.
4. Ask the local model for a short complete value and literal supporting quotations from a minimal source set. Documents are data, not executable instructions.
5. Reject fabricated quotations, unsupported values and unknown source paths. Keep necessary identifier bridges; drop an extra bridge when its identifier was already supplied in the question. An empty corpus refuses without invoking the model.

The base image, model revision and dependency versions are pinned. Weights are shipped inside the image and runtime downloads are disabled. No hosted inference API is used.

Image transcription must reach an end token before it is indexed. An interrupted generation gets one retry within a shared 500-second indexing budget; a second interruption skips that image instead of storing partial text.

Current limits: scanned PDFs without extractable text are not OCR-rendered; formula cells are represented as formula text rather than evaluated. Citation grounding checks do not prove semantic correctness. Tests and eventual GPU measurements must be considered separately.

Run unit/integration tests in an environment with pypdf, python-docx and openpyxl:

```sh
python3 -m unittest discover -s matches/rag/tests -v
```

Build from the repository root with `-f matches/rag/Dockerfile`. Registry image references are supplied privately, not committed here.
