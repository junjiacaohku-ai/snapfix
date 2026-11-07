# Background Research

Reviewed on 30 October 2026. This section distinguishes documented capabilities from the team's proposed design. It is based on primary-source documentation, not a hands-on comparative product test.

## Three applications available to users

| Application | Documented capabilities | Limitation or question relevant to SnapFix | Implication for our design |
|---|---|---|---|
| iFixit / FixBot | Step-by-step repair guidance, visual assistance and a repair knowledge base. Its announcement acknowledges uneven guidance for less well-covered products. [1] | A guide or answer must still be checked against the exact device. We have not verified whether every rental handoff requirement is supported. | Preserve device identity and evidence; present uncertainty before giving procedural guidance. |
| Frontdoor | Its mobile app connects users to repair experts by video, keeps call notes and recommends local professionals. [2] | A live consultation requires connectivity and an available expert. Service availability must be checked for the user's region; we have not tested it in Hong Kong. | Let users prepare device details and a bilingual repair request before contacting someone. |
| Google Lens | Image-based search can return information about objects, similar images, related websites and AI overviews. [3] | Visual similarity alone does not establish a model-specific fault or a validated repair procedure. This is a scope distinction, not a claim that the product lacks all safety or memory features. | Confirm model and error code before retrieval; use visual search only as supporting evidence. |

FixIt Lens remains an additional engineering reference: its repository describes vision/OCR, manual retrieval, safety checks and evaluation scripts. It is not counted among the three market applications above. [5]

## Motivation and proposed contribution

SnapFix targets a narrow household and rental workflow: identify a device, inspect supporting instructions, decide whether to seek help, and prepare a concise Chinese or English repair request. The proposed contribution is the integration and evaluation of that workflow for a small, explicit set of demonstration scenarios. We do not claim that repair decisions or bilingual reporting are unique across the entire market.

Source quality is a practical design constraint. Our audit found both PDF font decoding errors and a mismatch between the original washing-machine E24 scenario and Bosch's dishwasher documentation. Manufacturer pages and rendered manuals must therefore be checked rather than relying on extracted text alone. The current branch corrects the E24 demonstration category and records a source-bound correction of display-font characters; the model of an actual user's appliance remains unknown. [4]

Evaluation should distinguish evidence retrieval, safety policy, image quality and reporting. A successful mock response does not validate the live visual model. A correct manual page does not establish that a repair is safe. Public device photographs can support demonstrations, but photographs of working appliances do not become labelled fault examples merely because their filenames contain a scenario name.

The D-line deliverables include corpus provenance, repeatable extraction, labelled evaluation cases, source-attributed public photographs and reproducible results. The branch now includes rule-based safety checks, pixel-quality checks and persistent sessions. Live vision and mobile sharing still need end-to-end evaluation.

## Primary sources

1. iFixit, “Introducing FixBot,” 9 December 2025: https://www.ifixit.com/News/114700/introducing-fixbot
2. Frontdoor app support and FAQ: https://www.frontdoor.com/member-support; app listing: https://play.google.com/store/apps/details?id=com.frontdoor.app.prod
3. Google Search Help, “Search with an image on Google”: https://support.google.com/websearch/answer/1325808?hl=en
4. Bosch dishwasher instructions, document 9001014024 B, physical PDF page 35: https://media3.bosch-home.com/Documents/9001014024_B.pdf

5. FixIt Lens repository README, engineering reference: https://github.com/rakexhs/fixit-lens

The comparison does not assume that competitors lack safety controls, memory or repair handoff. Capabilities were checked in their published documentation; no hands-on comparative test was performed.
