# SnapFix Project Report

COMP7506A · Status on 30 October 2026

SnapFix helps people in rented homes turn an appliance problem into a clear next step and a repair request. The current backend supports six offline demonstration flows. This report covers the background research, application design and contributions recorded so far; the finished mobile workflow and member contributions will be updated before submission.

## Background Research

We reviewed three applications through their published documentation. The comparison focuses on finding useful instructions, deciding when to seek help and communicating a repair request. It is not a hands-on reliability comparison.

| Application | Relevant features | Improvement to explore in SnapFix |
|---|---|---|
| iFixit and FixBot | Repair guides and an assistant that accepts questions and photos. Available in the iFixit mobile app. [1] | Keep the exact device and manual page visible, and make uncertainty clear when coverage is limited. |
| Frontdoor | Video consultations with repair experts, saved call notes and referrals to local professionals. [2] | Help users prepare a concise request before contacting someone. A live consultation depends on connectivity and expert availability; local service coverage needs checking. |
| Google Lens | Visual search for objects, similar images and related websites. [3] | Ask for a model or error code before using a visually similar result as repair evidence. |

These applications already cover parts of the repair journey. Our design focuses on a small rental workflow: collect device information, show supporting instructions, decide whether professional help is needed, and prepare a Chinese or English request. We do not claim that any one feature is unique. Hong Kong service coverage and the quality of competing products have not been tested.

The open-source FixIt Lens project is an additional engineering reference for retrieval, safety checks and evaluation. It is not counted as one of the three market applications. [4]

Sources reviewed on 30 October 2026:

[1] [iFixit FixBot documentation](https://www.ifixit.com/Info/FixBot_Pro)

[2] [Frontdoor app support](https://www.frontdoor.com/member-support) and [Android app listing](https://play.google.com/store/apps/details?id=com.frontdoor.app.prod)

[3] [Google Lens help](https://support.google.com/websearch/answer/1325808?hl=en)

[4] [FixIt Lens repository](https://github.com/rakexhs/fixit-lens)

<!-- pagebreak -->

## Application Summary

**Category and motivation.** SnapFix is an information and household maintenance application. A tenant may know that a device is not working without knowing its model, the relevant instructions or how to explain the problem to a landlord. The design brings those details into one record and avoids presenting uncertain repair steps as confirmed advice.

**Design.** The planned mobile flow is capture or manual input, diagnosis, guidance, repair request and archive. Flutter supplies the mobile interface; FastAPI supplies the backend. PDF instructions are cleaned and split into text blocks with source pages, then indexed for retrieval. SQLite stores the corpus, sessions, feedback and report drafts.

**Current implementation.** Images are checked for brightness, sharpness and size. The demonstration chooses the diagnosis by upload filename; it does not run a live visual model. Safety rules can stop a response before procedural guidance is returned. The manual-entry E24 scenario is a Bosch dishwasher, with an unknown model and referral to professional help. The manufacturer source is document 9001014024 B, physical page 35. [5]

The six flows cover a router, dishwasher E24, BILLY furniture, microwave refusal, a retake prompt and bilingual reporting. Feedback is saved and included in report drafts. Sessions survive a service restart; deleting a session removes its related records. Photos are not stored or attached to generated reports, so the sender must attach them separately.

**Validation.** The corpus contains 16 source documents and 2,032 text blocks. The extraction audit records 45 sparse pages and 6 undecodable pages. A retrieval experiment on 30 router queries improved Hit@3 from 36.7% with the lexical baseline to 80% with BM25. Those queries cover one manual and do not establish accuracy across all devices. Four evidence-retrieval scenarios and two workflow-only cases are recorded separately.

The original safety set has 14 high-risk and 14 normal cases; all pass after correcting four missed refusals. Twenty additional regression cases also pass. The image experiment uses 13 unique public originals and 26 program-generated variants: brightness multiplied by 0.15 and Gaussian blur with a 12-pixel radius. All 13 darkened images triggered retake. Twelve blurred images could be assessed independently; all triggered retake. One original was already dark and was reported separately.

**Mobile integration.** The available FE-1 pull request contains the home, scan and preview foundation and an archive placeholder. Complete phone workflows, screenshots, real camera timing and system sharing still need integration testing. Public appearance images and modified images do not establish fault-recognition accuracy.

[5] [Bosch dishwasher instructions](https://media3.bosch-home.com/Documents/9001014024_B.pdf)

Implementation and results: `server/`, `server/experiments/`, `docs/data-handoff.md` and `docs/demo-runbook.md` in the project repository.

<!-- pagebreak -->

## Contributions

The following record distinguishes assigned responsibilities from submitted work. Pull requests are still under review. Each member should confirm the final description and add work completed outside GitHub before the course submission.

| Member and assigned area | Evidence recorded so far |
|---|---|
| Cao Junjia - BE-1 and team lead | PR #1 submits safety rules, provider adapters and an API contract draft. Final deployment and integration remain to be confirmed. |
| Shi Junying - BE-2 retrieval and storage | Assigned retrieval, SQLite, report endpoints and the source README. A final individual contribution record is still needed. |
| Zhu Yutaimin - FE-1 scan and diagnosis | PR #2 submits the Flutter project, theme components, home, scan and preview foundation. Its platform record confirms Windows and Android Emulator. |
| Yang Ruijia - FE-2 guidance and archive | Assigned guidance, archive, report screens, visual design and video editing. A final individual contribution record is still needed. |
| Zhang Fan - D data and content | PR #3 contains corpus collection and ETL, six mock flows, retrieval experiments, safety samples, public-image attribution, the image-quality experiment, English research and acceptance records. It also includes safety and persistence fixes, the demo runbook and this report draft. |

The D package includes replayable backend checks and a manifest that detects changed demonstration images. It uses a temporary database so repeating the checks does not erase saved sessions. The main and backup computers should each produce their own result file before the demonstration.

The remaining team evidence is specific: confirmed fault or assembly photos, completed phone acceptance records, meeting decisions, two timed rehearsals and each member's final contribution statement. The report will then be revised to describe the delivered application and include actual application screenshots.

### Contribution references

[PR #1](https://github.com/junjiacaohku-ai/snapfix/pull/1) - BE-1 safety and providers.

[PR #2](https://github.com/junjiacaohku-ai/snapfix/pull/2) - FE-1 Flutter foundation.

[PR #3](https://github.com/junjiacaohku-ai/snapfix/pull/3) - D data and validation package.

The team's report target is 26 November. The classroom demonstration is on 19 November; the team plans to submit before the 30 November course deadline. Each member must complete their own Moodle Peer Review Form.
