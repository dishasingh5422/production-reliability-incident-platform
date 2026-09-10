-- Daily availability percentage based on stored synthetic checks.
SELECT
    DATE(checked_at) AS check_date,
    ROUND(100.0 * SUM(CASE WHEN status = 'HEALTHY' THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS availability_percentage
FROM service_checks
GROUP BY DATE(checked_at)
ORDER BY check_date DESC;

-- Incident count by severity and state.
SELECT severity, status, COUNT(*) AS incident_count
FROM incidents
GROUP BY severity, status
ORDER BY severity, status;

-- Mean time to recover in minutes for resolved incidents.
SELECT
    ROUND(AVG(EXTRACT(EPOCH FROM (resolved_at - detected_at)) / 60.0), 2) AS mean_time_to_recover_minutes
FROM incidents
WHERE resolved_at IS NOT NULL;

-- Deployments associated with incidents detected within 30 minutes.
SELECT d.version, d.commit_sha, d.started_at, i.id AS incident_id, i.severity, i.detected_at
FROM deployment_events d
JOIN incidents i
  ON i.detected_at BETWEEN d.started_at AND d.started_at + INTERVAL '30 minutes'
ORDER BY i.detected_at DESC;

-- Open corrective actions.
SELECT i.id AS incident_id, i.short_description, c.action, c.owner, c.due_date, c.status
FROM corrective_actions c
JOIN incidents i ON i.id = c.incident_id
WHERE c.status <> 'COMPLETE'
ORDER BY c.due_date NULLS LAST;

