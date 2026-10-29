# D-line handoff to BE-2 and BE-1

## Reproduce

From `server/`, use Python 3.11+:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python corpus.py data/manifest.json data/chunks.json
python -m pytest tests -q
python experiments/run_retrieval.py
python experiments/evaluate_scenarios.py
python experiments/run_acceptance.py
```

Use the virtual environment's Python after activation. Experiments are offline and require no model API keys.

## Import contract

`manuals.json` exports `id, title, source, category`. `chunks.json` exports `id, manual_id, idx, text`, matching the PRD's `manual_chunks` fields. It additionally preserves `content` for existing evaluation callers and page, section, source URL, source SHA256 and extraction status for citations. `idx` is zero-based within each manual. Use `manual_id` to join; do not join by a title substring. The disposable SQLite round-trip test validates foreign keys and uniqueness, not BE-2's production storage implementation.

`manual_id` identifies a document, not an automatically recognized appliance. Header detection is heuristic. Diagram-heavy and sparse pages are flagged in `extraction-audit.json`; undecodable pages are excluded and recorded. A numeric PDF page is always available even where no reliable section title exists. `text-corrections.json` contains a visually checked, SHA-bound mapping for the Bosch display-font codes on PDF page 35. It is not a global character substitution.

## Reference retrieval

`retrieval.Retriever(rows).search(query, category=..., brand=..., error_code=..., manual_id=...)` provides a BE-2 reference implementation with bounded results, explicit metadata filters, brand aliases and exact error-code matching. `E:24` and `E24` normalize together; `E240` is distinct. An unknown manual ID or error code returns no results. The small Chinese expansion dictionary is explicit and does not constitute general translation. Only pass `manual_id` when it was verified upstream.

Do not generate repair instructions from a high-risk result. The microwave retrieval case checks safety evidence, while the production pipeline must refuse internal repair before generation.

## Safety integration

Run `experiments/evaluate_safety.py --gate /path/to/safety_gate.py --revision <commit> --output experiments/safety-results.json` against the chosen BE-1 revision. Nonzero exit means some cases failed, not that the evaluator crashed. Current evaluated revision and source hash are in the results file. This branch does not replace BE-1's implementation. The four false negatives are documented in `review-audit.md`.

## API changes requiring review

- E24 mock category corrected to `dishwasher`, decision `professional`; unknown actual model is retained as null.
- Unknown image filename now returns 422 instead of silently inventing Bosch E24.
- Unsupported manual brand/code returns 404; whitespace and E:24/E24 notation are normalized.
- Dark/blur filenames simulate a 422 retake response; this is not pixel analysis.
- Health always reports mock because this branch does not call a live provider.
- Report text asks the sender to attach a photo; the server does not claim it has attached one.

FE/BE-1 must acknowledge these semantics before merge. The data branch retains the existing response field names and endpoints. SQLite, the live provider, real image-quality checks and mobile screens remain outside this data branch.
