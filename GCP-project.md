**GCP authentication**
```bash
gcloud auth login --login-config=one-day-sandbox-gcloud.json
gcloud auth list
gcloud config get-value project
gcloud config get-value compute/region
```
**Env variable set**
```bash
export PROJECT_ID=$( gcloud projects list | awk 'NR>2{print $1}')
export REGION="europe-west1"
export REPOSITORY="python-doc-mgmt"
export BACKEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/backend:v1"
export FRONTEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/frontend:v1"
export GITHUB_OWNER="Devops-Practice2025"
export GITHUB_REPO="python-doc-mgmt"
gcloud projects describe "$PROJECT_ID"
gcloud config set project "$PROJECT_ID"
gcloud config set run/region "$REGION"
gcloud config list
```
**enable api**
```bash
gcloud services enable   artifactregistry.googleapis.com   cloudbuild.googleapis.com   run.googleapis.com   logging.googleapis.com
gcloud services list --enabled \
  --format='value(NAME)' |
grep -E 'artifactregistry|cloudbuild|run|logging'
```
**create repo and auth docker**
```bash
gcloud artifacts repositories create "$REPOSITORY" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Container images for python-doc-mgmt"

gcloud artifacts repositories list \
  --location="$REGION" \
  --project="$PROJECT_ID"

gcloud auth configure-docker \
  "${REGION}-docker.pkg.dev"
```
**Create the GitHub Actions service account**
```
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions deployment identity" \
  --project="$PROJECT_ID"
export SERVICE_ACCOUNT="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

##grant permission to push images to artifact registry

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/artifactregistry.writer"
# OIDC pool

gcloud iam workload-identity-pools create github \
  --location=global \
  --display-name="GitHub Actions" \
  --project="$PROJECT_ID"

export WORKLOAD_IDENTITY_POOL_ID="$(
  gcloud iam workload-identity-pools describe github \
    --location=global \
    --project="$PROJECT_ID" \
    --format='value(name)'
)"
echo "$WORKLOAD_IDENTITY_POOL_ID"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github \
  --display-name="GitHub repository provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository=='${GITHUB_OWNER}/${GITHUB_REPO}'" \
  --project="$PROJECT_ID"

##Allow the GitHub repository to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding \
  "$SERVICE_ACCOUNT" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${GITHUB_OWNER}/${GITHUB_REPO}" \
  --project="$PROJECT_ID"
export WORKLOAD_IDENTITY_PROVIDER="$(
  gcloud iam workload-identity-pools providers describe github-provider \
    --location=global \
    --workload-identity-pool=github \
    --project="$PROJECT_ID" \
    --format='value(name)'
)"

echo "GCP_PROJECT_ID=$PROJECT_ID"
echo "GCP_REGION=$REGION"
echo "GCP_WORKLOAD_IDENTITY_PROVIDER=$WORKLOAD_IDENTITY_PROVIDER"
echo "GCP_SERVICE_ACCOUNT=$SERVICE_ACCOUNT"


```

