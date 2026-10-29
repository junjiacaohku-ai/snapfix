# SnapFix Server

Python 3.11+. From this directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests -q
uvicorn main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs

## Runtime status

This branch always reports mock mode, including when an API key is present. It does not invoke a live vision provider. Sessions are in memory. SQLite and real provider integration are owned by BE-2 and BE-1.

Image fixture names: `router.jpg`, `e24.jpg`, `billy.jpg`, `microwave.jpg`, `dark.jpg`/`blur.jpg`, `report.jpg`. Arbitrary bytes are accepted for these mock fixtures; filenames route responses, not pixels. Unknown names return 422. Manual `Bosch`/`博世` + `E24`/`E:24` returns the corrected dishwasher scenario; unknown brand/code returns 404. E24 is not a verified washing-machine diagnosis.

Photos are not persisted. Report text asks the sender to attach a photo; the API has no attachment capability. These limitations must remain explicit during demonstrations.

## D-line tools

```sh
python corpus.py data/manifest.json data/chunks.json
python experiments/run_retrieval.py
python experiments/evaluate_scenarios.py
python experiments/run_acceptance.py
```

Extraction exports `manuals.json`, `chunks.json`, and `extraction-audit.json`. There are 15 manufacturer PDFs plus one government safety leaflet; they are not 16 unique supported models. Sparse/diagram-heavy pages require visual inspection. Unreadable pages are excluded and recorded. PDFium handles CID font fallback; one source-bound display-code correction was visually checked. No OCR engine or automatic diagram understanding is claimed.

BM25 reference retrieval is in `retrieval.py`; the original `weighted_matches` is retained as a lexical baseline for comparison. Full handoff instructions: `../docs/data-handoff.md`. Current evidence, limitations and team dependencies: `../docs/review-audit.md`.

The safety evaluator requires a separately supplied, reviewed BE-1 module:

```sh
python experiments/evaluate_safety.py --gate /path/to/safety_gate.py --revision COMMIT_SHA --output experiments/safety-results.json
```

It exits nonzero on failed cases. The committed results are an audit of the stated BE-1 revision, not a claim that the production pipeline is safe or that this branch implements the safety gate.
