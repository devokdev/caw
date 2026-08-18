# Module 06: Break Diagnosis - Failure A (Runaway Retry Loop)

## Diagnosis

### Symptoms Observed
1. When downstream dependency is degraded or slow, CPU and memory usage spikes steeply.
2. Log stream flooded with hundreds of retry attempts for a single request.
3. Node process / Asyncio event loop becomes completely starved and unresponsive.

### Root Cause
- The retry loop lacked an upper bound or was initialized with `max_retries = Infinity` / unbound while timer callbacks accumulated in memory without bounding backoff delay caps.

### Remediation Strategy
1. Enforce strict `max_retries = 3` cap.
2. Enforce strict `max_delay = 2000ms` exponential backoff cap.
3. Integrate randomized `jitter` (+/-50ms) to prevent synchronized retries and thundering herds.
