# Operations dashboard

Open `http://127.0.0.1:8080/dashboard` after starting the application. The root URL redirects to the same control room.

## What it shows

- Current operational or degraded service state and active controlled fault.
- Synthetic-check pass rate for qualifying checks recorded during the latest 24-hour window.
- Average response time for recent timed checks.
- Open-incident total and severity mix.
- Average time from detection to resolution for recent resolved incidents.
- Response-time trend, recent incidents, release evidence, and filterable check history.
- Local environment and application version.

The dashboard refreshes every 15 seconds. Each refresh calls readiness first, creating a current database-backed observation, and then fetches the bounded dashboard summary. The Refresh button performs the same operation immediately.

## Metric boundaries

| Metric | Definition | Boundary |
|---|---|---|
| Check pass rate | Healthy qualifying checks divided by healthy, failed, critical, or warning checks in the latest 24 hours | Synthetic monitoring evidence; not an availability SLA |
| Average response | Mean response time from recent checks that contain latency evidence | Small local sample, not load-test performance |
| Open incidents | Recent incidents with OPEN or ACKNOWLEDGED status | Mock incident store unless ServiceNow is configured |
| Average MTTR | Mean time between detection and resolution for recent resolved incidents | Controlled local simulation |

## Interview demonstration

1. Start on the all-systems-operational banner and explain liveness versus readiness.
2. Point to the check pass rate and explicitly state that controlled failures remain visible in the window.
3. Use the Attention filter to isolate failed and critical observations.
4. Show that the incident created by the PowerShell drill is resolved, not duplicated.
5. Connect the MTTR and incident timestamps to the RCA.
6. Open the API console from the sidebar to show the underlying contracts.

## Security and deployment

The browser receives read-only operational summaries. It does not receive the fault-injection token and provides no administrative fault controls. The dashboard ships inside the FastAPI container, so it is validated by the same Docker and GitHub CI builds. A public dashboard is intentionally not published while the API and PostgreSQL runtime remain local; publishing a disconnected static screen would not be live evidence.
