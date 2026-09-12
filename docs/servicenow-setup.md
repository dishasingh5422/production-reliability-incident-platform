# ServiceNow Personal Developer Instance setup

The repository contains a ServiceNow Table API adapter, but no live PDI was available during baseline verification.

Set these values outside version control:

```text
INCIDENT_PROVIDER=servicenow
SERVICENOW_INSTANCE_URL=https://YOUR_INSTANCE.service-now.com
SERVICENOW_USERNAME=YOUR_USERNAME
SERVICENOW_PASSWORD=YOUR_PASSWORD
```

## Verification sequence

1. Obtain a ServiceNow PDI and use a dedicated test user where possible.
2. Submit one controlled failed check and confirm one incident is created.
3. Repeat the failure and confirm the same incident is updated.
4. Submit two healthy checks and confirm it resolves.
5. Capture only safe fields: number, state, priority, timestamps, service, and redacted diagnostics.

The adapter and mocked HTTP contract may be described as tested. ServiceNow may be described as live only after this sequence succeeds against the user's PDI.

