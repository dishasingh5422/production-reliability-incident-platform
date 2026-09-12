# RCA: Controlled readiness failure

**Incident:** Local mock incident 2 (`MOCK-F9BA6370426C`)  
**Date:** 11 September 2026 IST / 10 September 2026 UTC  
**Severity:** High under demonstration rules  
**Status:** Resolved  
**Environment:** Local Docker Compose with PostgreSQL and PowerShell container

## Executive summary

A guarded readiness fault was deliberately activated. The process stayed healthy while `/readyz` returned HTTP 503. PowerShell detected the failure, returned critical exit code 2, and created one high-severity mock incident. After recovery, two healthy checks resolved the same incident. No customer, bank, or production system was involved.

## Impact

Synthetic only: a traffic manager using readiness would remove this instance from eligible traffic while keeping the process alive for diagnosis.

## Detection and timeline

| UTC time | Event |
|---|---|
| 23:33:05.259 | Controlled readiness fault activated |
| 23:33:06.598 | PowerShell observed HTTP 503 |
| 23:33:06.632 | One high-severity incident created |
| 23:33:07 | Guarded recovery endpoint removed the fault |
| 23:33:08.086 | First healthy check; recovery pending |
| 23:33:09.561 | Second healthy check |
| 23:33:09.592 | Same incident resolved |

- Approximate MTTD: 1.37 seconds.
- Approximate MTTR from incident creation: 2.96 seconds.
- Human acknowledgement was not modelled, so MTTA is not claimed.

## Root cause

The immediate cause was an intentional process-local readiness override. The API correctly returned `CONTROLLED_READINESS_FAILURE`, distinguishing the drill from a real PostgreSQL outage.

## Resolution

The authenticated recovery endpoint removed the override. PostgreSQL was rechecked and two healthy observations met the recovery threshold.

## What worked

- Liveness remained available for diagnosis.
- Readiness returned a safe specific code.
- PowerShell used critical exit code 2.
- Repeated failures did not duplicate incidents.
- One healthy check did not close the incident.
- SQL records preserved the timeline.

## Preventive action

**Action:** Retain regression tests proving health remains available during controlled readiness/application failures.  
**Owner:** Repository maintainer  
**Status:** Complete  
**Evidence:** `test_controlled_error_affects_status_not_health` and `test_controlled_readiness_failure_and_recovery`, included in the locally and remotely passing 16-test suite.

## Limitations

Timings are same-machine automation, the external reference is from the mock adapter, and no real load balancer, GCP alert, or ServiceNow notification delay was measured.

