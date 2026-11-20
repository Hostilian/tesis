# Agent skills review — research workflow, 20 Nov 2026

No installer scripts, lifecycle hooks, third-party API calls, Grafana Cloud services, OpenRouter models, credentials or billed services were executed or enabled. Academic and public/private boundaries preserved.

| Source | Specific inspected material | License | Reviewed outcome |
|---|---|---|---|
| [Ponytail canonical](https://github.com/DietrichGebert/ponytail) | [skills/ponytail/SKILL.md](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md) and README | MIT | **Adopt the reuse ladder** in repository-local minimal original skill; no global installation, hooks or marketplace trust implied |
| [StarQuant/ponytail-skill](https://github.com/StarQuant/ponytail-skill) | README points to DietrichGebert canonical upstream | MIT via GitHub API | Not selected as installation source; use canonical maintained repo |
| [Grafana Skills](https://github.com/grafana/skills) | README lists `alloy`, `dashboarding`, `promql`, and `audit-and-reduce-dependencies` among others | Apache-2.0 via GitHub API | **Defer deployment**, but `audit-and-reduce-dependencies` and `alloy` are likely useful later if actual observability needed. Do not install an entire observability platform to monitor static Pages |
| [Grafana GCX](https://github.com/grafana/gcx) | README describes CLI for real Grafana resources and endpoint compatibility; some Cloud features billed | Apache-2.0 via GitHub API | No Grafana deployment credentials or runtime necessary today. No live measurements claimed |
| [OpenRouter Skills](https://github.com/OpenRouterTeam/skills) | README: models, pricing, analytics, SDK, voice/image, agent harness | License text not fully verified | **Read-only documentation only**; no account, key, model routing or paid inference. No private data to AI providers |

Why the choice matters: **we added no geospatial runtime packages** and reused `rasterio`, `pystac-client`, `planetary-computer`, `numpy`, existing geospatial preprocessing, and the existing Leaflet visualization. User-specific code was limited to paired-scene provenance/QA and research-specific presentation. A separate mathematical QA run corrected Sentinel-2 processing-baseline reflectance conversion.

**Current observability decision:** GitHub Actions job exit/output, source manifests and errors provide sufficient operational evidence for the bounded local research experiment. A Grafana agent/Alloy exporter is unjustified without a persistent backend and real telemetry. If an authorized private runtime later exists, review Alloy (not obsolete Grafana Agent/Promtail), metrics fields and secret controls first.

**Current AI routing decision:** no integration until zero-cost eligibility and explicit privacy/account limits are demonstrated; model agreement never validates satellite findings.

**Review status:** original selected upstream skill files inspected; dependency/license/third-party asset audit remains incomplete; no installed skill hooks have been tested.
