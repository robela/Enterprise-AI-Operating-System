# Cloud Build Deployment History & Status Guide

## Current Deployment Status

### ✅ Confirmed Active Deployments

**Staging Environment (develop branch):**
- **Backend Service**: `enterprise-ai-backend-staging`
- **URL**: https://enterprise-ai-backend-staging-397980615504.us-central1.run.app/
- **Status**: ✅ Deployed and Responding
- **Verified**: test_backend.py confirms service is accessible

**GCP Project**: `main-presence-500410-f8`  
**Region**: `us-central1`

---

## Cloud Build Pipeline Configuration

### Build Triggers Setup

**Production Builds (main branch)**
```bash
# Trigger name: deploy-production
# Branch pattern: ^main$
# Deploys: enterprise-ai-backend, enterprise-ai-worker, enterprise-ai-frontend
```

**Staging Builds (develop branch)**
```bash
# Trigger name: deploy-staging
# Branch pattern: ^develop$
# Deploys: enterprise-ai-backend-staging, enterprise-ai-worker-staging, enterprise-ai-frontend-staging
```

### One-Time Setup Commands (if needed)

```bash
# 1. Connect GitHub Repository
gcloud builds repositories create enterprise-ai-repo \
  --remote-uri=https://github.com/robela/Enterprise-AI-Operating-System \
  --connection=github-connection \
  --region=us-central1 \
  --project=main-presence-500410-f8

# 2. Create Production Trigger
gcloud builds triggers create github \
  --name=deploy-production \
  --region=us-central1 \
  --repository=projects/main-presence-500410-f8/locations/us-central1/connections/github-connection/repositories/enterprise-ai-repo \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml \
  --project=main-presence-500410-f8

# 3. Create Staging Trigger
gcloud builds triggers create github \
  --name=deploy-staging \
  --region=us-central1 \
  --repository=projects/main-presence-500410-f8/locations/us-central1/connections/github-connection/repositories/enterprise-ai-repo \
  --branch-pattern="^develop$" \
  --build-config=cloudbuild.yaml \
  --project=main-presence-500410-f8
```

---

## How to Check Build History

### Method 1: gcloud CLI (Recommended)

**List recent builds:**
```bash
gcloud builds list \
  --project=main-presence-500410-f8 \
  --limit=10 \
  --format=table(id,status,createTime,substitutions.BRANCH_NAME)
```

**Get detailed logs for a specific build:**
```bash
# Replace BUILD_ID with actual ID from list above
gcloud builds log BUILD_ID \
  --project=main-presence-500410-f8 \
  --stream
```

**Get build summary (without streaming):**
```bash
gcloud builds describe BUILD_ID \
  --project=main-presence-500410-f8 \
  --format=json
```

**Find failed builds:**
```bash
gcloud builds list \
  --project=main-presence-500410-f8 \
  --filter="status:FAILURE" \
  --limit=10 \
  --format=table(id,status,failureMessage,createTime)
```

---

### Method 2: Google Cloud Console (Web UI)

**Visit Cloud Build Dashboard:**
```
https://console.cloud.google.com/cloud-build/builds?project=main-presence-500410-f8
```

**View Build Triggers:**
```
https://console.cloud.google.com/cloud-build/triggers?project=main-presence-500410-f8
```

---

## Cloud Build Pipeline Stages

### Build Execution Order

```
1. [set-env] Resolve environment from branch
   ├─→ Determines if production or staging
   └─→ Sets service names

2. [build-backend] Multi-stage Docker build
   ├─→ Builder stage: Install dependencies from pyproject.toml
   └─→ Runtime stage: Copy artifacts to slim image

3. [build-frontend] Next.js build
   ├─→ Builds with TypeScript/React
   └─→ Creates production-ready container

4. [push-backend] Push to Artifact Registry
   └─→ us-central1-docker.pkg.dev/main-presence-500410-f8/enterprise-ai/backend:{SHA,BRANCH}

5. [push-frontend] Push to Artifact Registry
   └─→ us-central1-docker.pkg.dev/main-presence-500410-f8/enterprise-ai/frontend:{SHA,BRANCH}

6. [deploy-backend] Deploy to Cloud Run
   ├─→ Image: backend:{SHORT_SHA}
   ├─→ Memory: 1Gi
   ├─→ CPU: 1
   ├─→ Instances: 0-10 (auto-scale)
   └─→ Port: 8060

7. [deploy-worker] Deploy Celery Worker
   ├─→ Same image as backend
   ├─→ Command: celery -A backend.workers.celery_app worker
   ├─→ Instances: 1-5
   └─→ Configured as internal (no-allow-unauthenticated)

8. [get-backend-url] Capture backend service URL
   └─→ Used to configure frontend NEXT_PUBLIC_BACKEND_URL

9. [deploy-frontend] Deploy to Cloud Run
   ├─→ Image: frontend:{SHORT_SHA}
   ├─→ Memory: 512Mi
   ├─→ CPU: 1
   ├─→ Port: 3000
   └─→ Instances: 0-5
```

---

## Environment Variables by Build

### Backend & Worker Deployment
```yaml
APP_ENV: staging|production
APP_DEBUG: false
REDIS_URL: redis://10.0.0.3:6379/0
STORAGE_BACKEND: gcs
GCS_BUCKET: enterprise-ai-documents-staging|enterprise-ai-documents
GCS_PROJECT_ID: main-presence-500410-f8
MESSAGING_BACKEND: pubsub
CORS_ORIGINS: http://localhost:3000
```

### Secrets (from Cloud Secret Manager)
```yaml
APP_SECRET_KEY
JWT_SECRET_KEY
DATABASE_URL
OPENAI_API_KEY
```

### Frontend Deployment
```yaml
NEXT_PUBLIC_BACKEND_URL: [dynamically populated from backend deployment]
```

---

## Monitoring & Troubleshooting

### Check Service Status

**List all deployed services:**
```bash
gcloud run services list \
  --region=us-central1 \
  --project=main-presence-500410-f8 \
  --format=table(metadata.name,status.conditions[0].status,metadata.createTime)
```

**Get service details:**
```bash
gcloud run services describe enterprise-ai-backend-staging \
  --region=us-central1 \
  --project=main-presence-500410-f8 \
  --format=json
```

**View service logs:**
```bash
gcloud run services describe enterprise-ai-backend-staging \
  --region=us-central1 \
  --project=main-presence-500410-f8 \
  --format="value(status.conditions[*].message)"
```

### Check Container Registry

**List images in Artifact Registry:**
```bash
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/main-presence-500410-f8/enterprise-ai \
  --project=main-presence-500410-f8
```

**List tags for a specific image:**
```bash
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/main-presence-500410-f8/enterprise-ai/backend \
  --include-tags \
  --project=main-presence-500410-f8
```

### Troubleshoot Failed Builds

**Find last failed build:**
```bash
gcloud builds list \
  --project=main-presence-500410-f8 \
  --filter="status:FAILURE" \
  --limit=1 \
  --format="value(id)"
```

**Get detailed error:**
```bash
# Get the BUILD_ID from above command
gcloud builds log BUILD_ID --project=main-presence-500410-f8 | tail -100
```

---

## Database & Infrastructure Connectivity

### Cloud SQL Connection
```
Connection: main-presence-500410-f8:us-central1:enterprise-ai-db
Configured: VPC Connector for secure access
```

### Redis (Memorystore)
```
Address: 10.0.0.3:6379
Access: Via VPC Connector
URL in Config: redis://10.0.0.3:6379/0
```

### VPC Connector
```
Resource: projects/main-presence-500410-f8/locations/us-central1/connectors/enterprise-ai-connector
Used by: Backend, Worker, Frontend services
```

---

## Quick Testing

**Test staging backend:**
```bash
python3 test_backend.py
```

**Manual endpoint tests:**
```bash
# Health check
curl https://enterprise-ai-backend-staging-397980615504.us-central1.run.app/health

# API documentation
curl https://enterprise-ai-backend-staging-397980615504.us-central1.run.app/docs

# Status endpoint
curl https://enterprise-ai-backend-staging-397980615504.us-central1.run.app/status
```

---

## Authentication & Setup

**Set default GCP project:**
```bash
gcloud config set project main-presence-500410-f8
```

**Check current authentication:**
```bash
gcloud auth list
gcloud config list
```

**Authenticate if needed:**
```bash
gcloud auth login
gcloud auth application-default login
```

---

## Recent Build History Commands

To get a quick summary of recent deployment history, run:

```bash
# Most recent 5 builds with details
gcloud builds list --project=main-presence-500410-f8 --limit=5 --format=json | \
  jq '.[] | {id, status, branch: .substitutions.BRANCH_NAME, created: .startTime, finished: .finishTime}'
```

Or for a simple table:
```bash
gcloud builds list \
  --project=main-presence-500410-f8 \
  --limit=10 \
  --sort-by=~createTime \
  --format="table(id,status,createTime,substitutions.BRANCH_NAME)"
```

---

## Notes

- **Staging deployments** happen automatically on every commit to `develop` branch
- **Production deployments** only trigger on commits to `main` branch
- **Build time**: ~5-10 minutes depending on cache hit
- **Image caching**: Uses branch name for incremental builds (faster rebuilds)
- **Auto-scaling**: Configured for cost optimization (0 min instances for frontend/API)

