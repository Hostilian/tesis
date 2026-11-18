# EIE67E thesis alignment — public evidence note

**Review date:** 18 November 2026  
**Status:** Course connection is evidenced; thesis-topic approval is not established by the course record.

## Course record and limits

CZU Moodle lists EIE67E Component-based Software Development for WS 2026/27. The detailed syllabus available in this review is from WS 2023/24, so current outcomes, assessment and language must be checked in the current course space.

The historical syllabus describes application design, reusable code and component libraries, UI/database work, design patterns, profiling, refactoring, unit testing and network/distributed-object topics. These outcomes can be demonstrated through one modular software pipeline. They do not approve a research topic, establish a formal computational limit or validate scientific findings.

The repository is primarily Python, while the historical syllabus specifies a C#/.NET project. Confirm current language requirements before claiming course compliance or changing implementation language.

## Course-to-project mapping

| Historical syllabus theme | Potential project evidence | Evidence needed |
|---|---|---|
| Reusable code and component libraries | Provider/catalogue adapters with shared interfaces | Source paths, interface contracts and tests |
| Application design | Small end-to-end public-data pipeline | Approved scope, architecture and reproducible run |
| UI creation | Map or results viewer, if retained | Working interaction, empty/error states and usability evidence |
| Databases and external data | Metadata/results persistence or clear file-based design | Schema or storage design and tested reads/writes |
| Design patterns and refactoring | Documented modular boundaries and justified patterns | Code review and before/after evidence where relevant |
| Profiling and debugging | Measured acquisition, preprocessing and detection costs | Repeated benchmark with environment and API latency separated |
| Unit testing | Offline tests for transforms, interfaces and provenance | Output tied to a known commit; fixtures visibly marked mock |
| Networking/distributed objects | API use, retries/timeouts, rate limits and cache behavior | Live integration evidence or an explicitly identified mock contract |

## Candidate component boundaries

This is an engineering proposal, not a claim that every component currently exists:

1. Provider adapter for a bounded, approved public observation.
2. Preprocessing for quality masks, required bands and compact features.
3. One transparent low-resource baseline chosen for the approved question.
4. Evaluation using an independently justified design.
5. Provenance for source IDs, dates, parameters, code revision and data mode.
6. Optional service/API and visualization with clear errors and mock/demo status.

A low-compute design can support the course connection through bounded processing, caching, chunked reads and profiling. No source reviewed establishes a formal compute cap.

## Verification items

- Obtain the formal assignment and confirm its approved question, objective, method and scope.
- Check current EIE67E materials for current learning outcomes, language and assessment.
- Identify what components are implemented, tested and live in the reviewed code.
- Separate software-quality evaluation from satellite-science validation.
- Do not infer enrollment, grades, credit transfer, topic approval or a compute restriction from public course information.

## Sources

- [CZU Moodle course listing](https://moodle.czu.cz/course/search.php?perpage=all&search=se)
- [Historical EIE67E syllabus, WS 2023/24](https://is.czu.cz/katalog/syllabus.pl?predmet=229754)
