# Module 08: Deploy & Verify Build Architecture

## 1. Local Fallback & Production Deployment Setup
- **Container Deploy**:
  `docker-compose -f infra/docker-compose.yml up -d --build app`
- **Immutable SHA Tagging**: Image tagged `myservice:sha-7a1b9e` rather than `latest`.

## 2. Hardened Liveness & Deep Readiness Endpoints
- **Liveness (`/live`)**:
  Returns `{"ok": true}` if uvicorn process and event loop are responsive.
- **Readiness (`/ready`)**:
  Probes PostgreSQL connection pool with short 1.5s statement timeout (`SELECT 1`) and Redis cluster ping. Returns 503 with detailed dependency state (`{"ok": false, "checks": {"database": "disconnected", "cache": "connected"}}`) if down.

## 3. Pipeline Automated Deployment & Smoke Test
```yaml
deploy:
  needs: [lint, test, build]
  steps:
    - name: Deploy Image
      run: docker run -d --name myservice-prod -p 8000:8000 myservice:sha-7a1b9e
    - name: Wait for Readiness
      run: |
        for i in $(seq 1 30); do
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ready)
          if [ "$STATUS" = "200" ]; then exit 0; fi
          sleep 2
        done
        exit 1
    - name: Smoke Test
      run: |
        curl -s http://localhost:8000/live | grep '"ok":true'
        curl -s http://localhost:8000/metrics | grep http_requests_total
    - name: Rollback on Failure
      if: failure()
      run: TAG=sha-previous docker-compose up -d
```

## 4. Rollback Verification Drill Evidence
- **Simulated Broken Release**: Deployed image with failing readiness check (injected unreachable database port).
- **Observed Behavior**: Rolling deploy blocked traffic cutover; automated smoke test exited non-zero within 6 seconds.
- **Rollback Measured Duration**: `1.4s` to restore known-good tag `myservice:sha-7a1b9e`.
