# Incident management

## Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Healthy
    Healthy --> Open: failed check
    Open --> Open: repeat failure updates evidence
    Open --> RecoveryPending: first healthy check
    RecoveryPending --> Open: failure recurs
    RecoveryPending --> Resolved: threshold reached
    Resolved --> Open: later failure creates new incident
```

## Deduplication and recovery

The key is SHA-256 of lowercase service, check type, and target. An incident is reused only while `OPEN` or `ACKNOWLEDGED`. The default recovery threshold is two consecutive healthy checks; another failure resets the counter.

## Provider boundary

`MockIncidentClient` is fully tested. `ServiceNowIncidentClient` uses the Table API with environment-loaded credentials. Payload construction is tested through a mock HTTP transport; live ServiceNow execution remains pending.

Severity rules are demonstration assumptions, not bank policy.

