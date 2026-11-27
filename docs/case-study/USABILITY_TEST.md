# Usability test kit: Portugal case-study page

This kit is for a small usability test of `docs/case-study/index.html`, published at `/tesis/case-study/`. **No test has been run yet.** The results table at the end is empty on purpose.

## 1. Purpose

The test checks whether a first-time reader can do three things on the page:

- find the key numbers;
- tell observations apart from derived results and interpretations;
- trace a number back to its source.

It is a small formative test meant to find problems. With 5 to 8 participants, the results describe those participants only. They do not support statistical claims about all users.

## 2. Set-up

- Use the published page or a local copy served with `python -m http.server --directory docs`. Write down the git commit of the page you test.
- Start every session on the Alqueva case with default settings: satellite basemap, only "Candidate change" switched on, opacity 85 %.
- Write down the device, browser, screen width and input method (mouse, touch, keyboard only, screen reader). Do not write down anything that identifies the person.
- Ask participants to think aloud. Do not help unless they are stuck for more than 2 minutes. Count any help as an assist.

## 3. Tasks

Read each task aloud. Start the clock when you finish reading and stop it when the participant gives a final answer.

The answer key comes from the run outputs in `docs/case-study/data/` (observation-derived results, runs of 2026-11-26). If the data are rerun, update the answers from the same keys.

| # | Task (read to participant) | Correct answer | Source | Success criteria |
|---|---|---|---|---|
| T1 | "Find how many hectares became greener in the Alqueva area between 2018 and 2025." | 2,260 ha (22.1 % of valid pixels) | `alqueva_olive/results.json`, `change.increase_area_ha`, `change.increase_share_of_valid` | **Success:** says about 2,260 ha. **Partial:** finds the right row but reads the wrong number, for example the decrease (372 ha). **Fail:** no answer, or a number from elsewhere. |
| T2 | "Look at the list of layers. Which ones are direct observations, which are computed results, and which are interpretations?" | Observations: both Sentinel-2 true-colour layers and COS 2025. Derived results: index difference, candidate change and change patches. Interpretation: the "Increase pixels stable May→Aug" row in Key numbers (no layer carries this label). | Badges on the page; `layerDefs` in `index.html` | **Success:** all 6 layers sorted correctly, and the participant uses the badges to do it. **Partial:** 4 or 5 correct. **Fail:** 3 or fewer correct, or the badges are not noticed. |
| T3 | "Switch to the mine area and show me where bare ground increased." | Choose "Neves-Corvo mine area" under Study area. The red areas are "BSI increase" (327 ha in total). | `neves_corvo_mine/results.json`, `web.legend.increase`, `change.increase_area_ha` | **Success:** switches the case without help and points to red areas, or opens an "increase patch" popup. **Partial:** switches the case but points to blue (decrease) areas, or needs an assist. **Fail:** cannot switch the case. |
| T4 | "Back in the Alqueva area: two images taken 20 days apart should show almost no change. What share of pixels did the method still flag for that pair?" | 0.86 % | `alqueva_olive/results.json`, `change.control_flagged_share_at_threshold` | **Success:** says 0.86 % and links it to false alarms or noise. **Partial:** finds the number but cannot say what it means. **Fail:** no answer. |
| T5 | "Find the catalogue entry for the 2025 image used in the Alqueva comparison." | The "STAC item" link for `S2C_29SNC_20250821_0_L2A` under Provenance. | `alqueva_olive/manifest.json`, `inputs` | **Success:** opens the right STAC item link. **Partial:** finds the Provenance section but opens a different item. **Fail:** does not find Provenance. |

After T5, ask one comprehension question: **"Does the map tell you why the land changed?"** The correct answer is no. The page shows where the surface signal changed, not why. Record the answer word for word.

## 4. What to record

For each participant and task, record:

- **time** in seconds;
- **outcome**: success, partial or fail, using the criteria above;
- **errors**: wrong clicks, wrong layer, wrong number read, wrong case;
- **assists**: how many times you helped;
- **quotes**: short think-aloud remarks, especially confusion about wording, badges or colours.

Then hand out the SUS questionnaire (section 5).

## 5. System Usability Scale (SUS)

The SUS is a 10-item questionnaire by Brooke (1996). Participants rate each statement from 1 (strongly disagree) to 5 (strongly agree). Read "system" as "this web page". Ask participants to answer every item quickly and to mark 3 if they are unsure.

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| 1 | I think that I would like to use this system frequently. | | | | | |
| 2 | I found the system unnecessarily complex. | | | | | |
| 3 | I thought the system was easy to use. | | | | | |
| 4 | I think that I would need the support of a technical person to be able to use this system. | | | | | |
| 5 | I found the various functions in this system were well integrated. | | | | | |
| 6 | I thought there was too much inconsistency in this system. | | | | | |
| 7 | I would imagine that most people would learn to use this system very quickly. | | | | | |
| 8 | I found the system very cumbersome to use. | | | | | |
| 9 | I felt very confident using the system. | | | | | |
| 10 | I needed to learn a lot of things before I could get going with this system. | | | | | |

**Scoring (Brooke 1996):**

1. For odd items (1, 3, 5, 7, 9), the item score is the answer minus 1.
2. For even items (2, 4, 6, 8, 10), the item score is 5 minus the answer.
3. Add the 10 item scores (range 0 to 40) and multiply by 2.5. The result runs from 0 to 100.

A SUS score is not a percentage. Report each participant's score, the median and the range. With so few participants, do not compare the mean with published benchmarks.

## 6. Consent and anonymity

Read this to each participant before you start:

> This is a test of a web page, not of you. It takes about 20 minutes. You can stop at any time without giving a reason. I will write down times, answers and short quotes, but not your name. Your results will appear in my bachelor thesis only under a code such as P01. I will not record your face or voice.

- Get spoken or written consent before the first task. Keep any signed form and the list linking codes to people off this repository. Store them locally (for example in `docs/thesis_audit/`, which is never committed) or on paper.
- Do not record screens, faces or voices unless you ask for that separately and the participant agrees.
- Only anonymised codes and the measures below go into this file or the thesis.
- Check with the supervisor whether the faculty needs ethics approval for a test like this.

## 7. Results (to be filled in)

Page commit tested: _______ Date range: _______

| Participant | Device / input | T1 time (s) / outcome | T2 time (s) / outcome | T3 time (s) / outcome | T4 time (s) / outcome | T5 time (s) / outcome | "Why?" answer | SUS score | Notable quotes or errors |
|---|---|---|---|---|---|---|---|---|---|
| P01 | | | | | | | | | |
| P02 | | | | | | | | | |
| P03 | | | | | | | | | |
| P04 | | | | | | | | | |
| P05 | | | | | | | | | |

Summary per task (fill in after all sessions): success rate, median time, most common error.

## Reference

Brooke, J. (1996). SUS: A "quick and dirty" usability scale. In P. W. Jordan, B. Thomas, B. A. Weerdmeester and I. L. McClelland (Eds.), *Usability Evaluation in Industry* (pp. 189–194). London: Taylor & Francis. https://doi.org/10.1201/9781498710411-35
