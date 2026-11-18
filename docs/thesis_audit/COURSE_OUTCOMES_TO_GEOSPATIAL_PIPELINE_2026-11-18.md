# Public course-outcome crosswalk for a geospatial thesis pipeline

**Review date:** 18 November 2026  
**Status:** Public-syllabus-based design crosswalk. It does not claim that any individual enrolled in, passed, or received credit for these units, and it does not change a formal thesis assignment.

## One integrated pipeline, multiple course outcomes

The curriculum connections can be represented by one source-to-result software pipeline. Each course contributes a different competency; the thesis still needs one approved research question and a bounded study design.

| Course unit | Public catalogue learning outcome | Concrete thesis artefact | Current project evidence and gap |
|---|---|---|---|
| INF13186L — Interação Pessoa-Máquina (Human-Computer Interaction) | Identify users and tasks, design interfaces, and evaluate interfaces throughout development. | A map/dashboard with task flows, accessible controls, and a small usability evaluation protocol. | The repository includes a dashboard in docs/app.js; no user/task or usability-evaluation evidence is established. |
| INF13204L — Metodologias e Desenvolvimento de Software (Methods and Software Development) | Requirements, modeling, design/implementation, software patterns, configuration management, testing and validation. | A requirements-to-component trace with explicit interfaces, configuration, offline fixtures, and verification records. | Python modules for ingestion, preprocessing, anomaly analysis, provenance, API and tests are present. Presence does not establish live-provider behavior. |
| INF13207L — Tecnologias Web (Web Technologies) | Web foundations, client/server protocols, frameworks, application servers, MVC and usability. | A documented API contract, client/server flow, map view, error behavior and deployment description. | FastAPI source and browser UI exist; some background processing is simulated, so production claims need separate evidence. |
| INF14387L — Transformação e Análise de Dados (Data Transformation and Analysis) | Data-quality assessment; handling missing values, outliers and class imbalance before analysis or machine learning. | A raster quality gate for date, CRS, bands, resolution, clouds, NoData, and reproducible transformations. | Existing Sentinel preprocessing computes spectral indices and masks clouds. Cross-sensor checks and authenticated imagery integration remain unverified. |
| MAT02354L — Probabilidade e Estatística (Probability and Statistics) | Probability and statistical inference, hypothesis formulation, and data analysis under uncertainty. | A sampling plan, uncertainty reporting, appropriate evaluation design, and limits on interpretation. | Detector code mentions bootstrap uncertainty. The empirical thesis metrics have not been independently reproduced by this document. |
| EIE67E — Component-based SW Development | The retrieved 2023/24 syllabus describes reusable code/components, application design, UI/database work, design patterns, profiling, refactoring and testing. | Reusable source adapters, preprocessing, evaluation, provenance, API/UI and a measured resource profile. | The repository is primarily Python, while that historical syllabus lists C#/.NET. Current 2026/27 course requirements must be checked. |

## Course catalogue sources

- [INF13186L — Interação Pessoa-Máquina](https://www.uevora.pt/estudar/cursos/unidades-curriculares-isoladas/unidades-curriculares-isoladas-por-curso?curso=2614&uc=INF13186L)
- [INF13204L — Metodologias e Desenvolvimento de Software](https://www.uevora.pt/estudar/cursos/unidades-curriculares-isoladas/unidades-curriculares-isoladas-por-curso?curso=2614&uc=INF13204L)
- [INF13207L — Tecnologias Web](https://www.uevora.pt/internacionalizar/Mobilidade-In/Mobilidade-de-Estudantes/unidades-curriculares-oferecidas-por-curso?curso=2570&uc=INF13207L)
- [INF14387L — Transformação e Análise de Dados](https://www.uevora.pt/estudar/cursos/unidades-curriculares-isoladas/unidades-curriculares-isoladas-por-curso?curso=2629&uc=INF14387L)
- [MAT02354L — Probabilidade e Estatística](https://www.uevora.pt/estudar/estudantes-ue/optativas-livres?curso=2614&uc=MAT02354L)
- [CZU EIE67E current listing](https://moodle.czu.cz/course/search.php?perpage=all&search=se); [detailed 2023/24 syllabus](https://is.czu.cz/katalog/syllabus.pl?predmet=229754)

Catalogue records establish publicly stated course content only. They do not establish a particular student's enrolment, grade, completion, transfer, or recognition.

## Evidence and academic-integrity limits

- A course fit is not evidence that its techniques were implemented correctly or that the scientific result is valid.
- A software test can validate code behavior on its inputs; synthetic fixtures cannot validate real-world agronomic outcomes.
- UI code is not usability evidence; API code is not proof of a working external integration; a module called provenance is not a complete audit trail without a traceable run.
- The current thesis assignment and current course requirements control the scope and allowed AI assistance.
- Results, discussion, and conclusion must be authored from real work by the student under the applicable CZU AI-use directive.

Sources for implementation inventory: [pipeline preprocessing](https://github.com/Hostilian/tesis/blob/main/pipeline/src/preprocessing.py), [pipeline API](https://github.com/Hostilian/tesis/blob/main/pipeline/src/api_server.py), [anomaly orchestrator](https://github.com/Hostilian/tesis/blob/main/pipeline/src/anomaly_detector.py), and [dashboard source](https://github.com/Hostilian/tesis/blob/main/docs/app.js).

