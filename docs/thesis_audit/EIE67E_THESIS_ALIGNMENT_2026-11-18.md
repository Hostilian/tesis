# EIE67E thesis alignment - evidence-based working note
**Review date:** 18 November 2026  
**Status:** Course connection is evidenced; thesis-topic approval is not established by the course record.

## Finding

The strongest class connection found in the user's prior thesis context is EIE67E Component-based SW Development. CZU Moodle lists EIE67E for WS 2026/27 and identifies Jir� Brozek as guarantor. The retrievable formal syllabus is from WS 2023/24, so its detailed outcomes and assessment must be checked against the current course space.

The historical syllabus describes application design, reusable code, component libraries, UI/database work, design patterns, profiling, refactoring and unit testing, and includes network/distributed-object topics. Those software-engineering outcomes can be demonstrated by a modular satellite-data pipeline. They do not themselves approve a satellite-research topic, establish a computational-power rule or validate scientific findings.

## Course-to-project mapping

| EIE67E theme in the retrieved syllabus | Potential project evidence | Evidence needed before making a thesis claim |
|---|---|---|
| Reusable code and component libraries | Provider/catalogue adapters with shared interfaces | Source paths, interface contracts and tests |
| Application design | Small end-to-end open-data pipeline | Approved scope, architecture and reproducible run |
| UI creation | Map/dashboard or results viewer, if retained in the final scope | Working interaction, empty/error states and usability evidence |
| Databases and external data | Metadata/results persistence or a clear file-based alternative | Schema or storage design, tested reads/writes |
| Design patterns and refactoring | Documented modular boundaries and justified patterns | Code review, before/after evidence where relevant |
| Profiling and debugging | Measured acquisition, preprocessing and detection costs | Repeated benchmark record with environment and API latency separated |
| Unit testing | Offline tests for transforms, interfaces and provenance | Test output tied to a known commit; fixtures visibly marked mock |
| Networking/distributed objects | API use, retries/timeouts, rate limits and cache behavior | Live integration evidence or explicitly identified mock contract |
| Choosing tools for the problem | Comparison of API, runtime and model choices | Criteria, evidence, trade-offs and assignment fit |

## Candidate component boundaries

The following is an engineering proposal to compare with actual code, not a claim that every component currently exists:

1. Catalogue/provider adapter: search and retrieve a bounded set of public observations.
2. Preprocessing: mask quality issues, select required bands and derive compact features.
3. Detector: a transparent, low-resource baseline selected for the approved research question.
4. Evaluation: calculations and plots using an independently justified evaluation design.
5. Provenance: persist source IDs, dates, parameters, code revision and data mode.
6. Service/API and visualization: expose clearly labeled outputs, errors and mock/demo status.

A low-compute design can support the class connection through bounded processing, caching, chunked reads and profiling. No source reviewed establishes a formal compute cap or identifies the "first guy" who may have mentioned it.

## Supervisor work check

The official CZU teaching profile lists Jir� Brozek as guarantor of EIE67E and lists teaching in computer principles, computer architecture and object modelling. A public Theses.cz search result indexes a 2012 CZU PEF dissertation by the same name titled "Distribuovan� objektov� architektury" ("Distributed Object Architectures"). Its direct record and contents were not accessible in this check. Treat it as a lead until the institutional record is verified; no verified master's thesis record was located.

This work history may justify checking component and distributed-architecture concepts for technical fit. It does not show that the supervisor expects a satellite-API thesis or has approved a particular method.

## Open verification items

- Obtain the exact current UIS thesis assignment and confirm the approved title, objective, method and scope.
- Open the current EIE67E 2026/27 syllabus or Moodle materials and confirm learning outcomes and assessment.
- Locate the source that names "the first guy" and states a computational limit; do not infer identity from unrelated old course records.
- Verify the direct Theses.cz/CZU record and contents for the 2012 dissertation before citing it.
- Identify what components are actually implemented and tested in the current reviewed branch.
- Separate software-quality evaluation from satellite-science validation.

## Sources

- [CZU Moodle course listing for WS 2026/27](https://moodle.czu.cz/course/search.php?perpage=all&search=se)
- [CZU EIE67E syllabus, WS 2023/24](https://is.czu.cz/katalog/syllabus.pl?predmet=229754)
- [Jir� Brozek's CZU teaching profile](https://home.czu.cz/brozekj/pedagogika?editmode=0)
- [Theses.cz related-work search for distributed architecture](https://theses.cz/th_search/prace_na_stejne_tema?ks=distribuovana+architektura)

