# Public course-outcome crosswalk for a geospatial thesis pipeline

**Review date:** 18 November 2026  
**Status:** Public-syllabus-based design crosswalk. It does not claim that any individual enrolled in, passed, or received credit for these units, and it does not change a formal thesis assignment.

## One integrated pipeline, multiple course outcomes

The course connections can be represented by one coherent source-to-result software system that supports the full approved thesis aims. The registered assignment may contain several connected objectives or questions; do not replace them with one smaller question by default. Course outcomes bound relevant work packages, and weak or irrelevant course mappings should be omitted.

| Course unit | Proposed relevance | Possible thesis artefact | Include in the thesis map only when |
|---|---|---|---|
| INF13186L — Interação Pessoa-Máquina (Human-Computer Interaction) | Conditional | User/task definition, interface design, and a permitted evaluation protocol | A genuine, relevant interface-evaluation contribution is feasible; otherwise omit |
| INF13204L — Metodologias e Desenvolvimento de Software (Methods and Software Development) | Direct-fit candidate | Requirements-to-component trace, design decisions, configuration, and verification records | Current learning outcomes match the documented software work |
| INF13207L — Tecnologias Web (Web Technologies) | Conditional | API contract, client/server flow, error handling, or web-map behaviour | The API/web deliverable remains a relevant part of the approved thesis |
| INF14387L — Transformação e Análise de Dados (Data Transformation and Analysis) | Direct-fit candidate | Per-modality quality gates and reproducible transformations across relevant imagery | Real metadata/examples and the assignment's methods support the task |
| MAT02354L — Probabilidade e Estatística (Probability and Statistics) | Direct-fit candidate | Sampling, assumptions, uncertainty, and a justified evaluation design | The approved aims and independent reference support statistical inference |
| EIE67E — Component-based SW Development | Direct-fit candidate; current requirements unresolved | Reusable source/modality adapters, shared provenance/quality services, and measured software quality | Current 2026/27 outcomes/language are confirmed and the artefacts fit them |

## Course catalogue sources

- [INF13186L — Interação Pessoa-Máquina](https://www.uevora.pt/estudar/cursos/unidades-curriculares-isoladas/unidades-curriculares-isoladas-por-curso?curso=2614&uc=INF13186L)
- [INF13204L — Metodologias e Desenvolvimento de Software](https://www.uevora.pt/estudar/cursos/unidades-curriculares-isoladas/unidades-curriculares-isoladas-por-curso?curso=2614&uc=INF13204L)
- [INF13207L — Tecnologias Web](https://www.uevora.pt/internacionalizar/Mobilidade-In/Mobilidade-de-Estudantes/unidades-curriculares-oferecidas-por-curso?curso=2570&uc=INF13207L)
- [INF14387L — Transformação e Análise de Dados](https://www.uevora.pt/estudar/cursos/unidades-curriculares-isoladas/unidades-curriculares-isoladas-por-curso?curso=2629&uc=INF14387L)
- [MAT02354L — Probabilidade e Estatística](https://www.uevora.pt/estudar/estudantes-ue/optativas-livres?curso=2614&uc=MAT02354L)
- [CZU EIE67E current listing](https://moodle.czu.cz/course/search.php?perpage=all&search=se); [detailed 2023/24 syllabus](https://is.czu.cz/katalog/syllabus.pl?predmet=229754)

Catalogue records establish public course content only; they do not establish an individual's enrolment, grade, completion, transfer, or recognition. The unit mappings above are suggestions for teacher review, not a requirement to include every course. Keep only direct fits and omit any weak mapping.

## Evidence and academic-integrity limits

- A course fit is not evidence that its techniques were implemented correctly or that the scientific result is valid.
- A software test can validate code behavior on its inputs; synthetic fixtures cannot validate real-world agronomic outcomes.
- UI code is not usability evidence; API code is not proof of a working external integration; a module called provenance is not a complete audit trail without a traceable run.
- The current thesis assignment and current course requirements control the scope and allowed AI assistance.
- Results, discussion, and conclusion must be authored from real work by the student under the applicable CZU AI-use directive.

Sources for implementation inventory: [pipeline preprocessing](https://github.com/Hostilian/tesis/blob/main/pipeline/src/preprocessing.py), [pipeline API](https://github.com/Hostilian/tesis/blob/main/pipeline/src/api_server.py), [anomaly orchestrator](https://github.com/Hostilian/tesis/blob/main/pipeline/src/anomaly_detector.py), and [dashboard source](https://github.com/Hostilian/tesis/blob/main/docs/app.js).

