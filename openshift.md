# Python Document Management Application — Red Hat OpenShift Deployment Guide

This document describes the complete process for deploying the `python-doc-mgmt` application to a Red Hat OpenShift cluster from scratch.

Repository:

```text
https://github.com/Devops-Practice2025/python-doc-mgmt.git
```

---

# 1. Application Architecture

The application consists of three main components:

- Frontend
- Backend
- PostgreSQL database

The OpenShift architecture is:

```text
                         Internet
                            |
                          HTTPS
                            |
                            v
                    OpenShift Router
                            |
                            v
                    OpenShift Route
                     document-mgmt
                            |
                            v
                    frontend Service
                     ClusterIP :80
                            |
                      targetPort 5000
                            |
                 +----------+----------+
                 |                     |
                 v                     v
           frontend Pod          frontend Pod
              :5000                 :5000
                 |
                 | HTTP
                 v
                  backend Service
                  ClusterIP :8000
                         |
                         v
                    backend Pod
                       :8000
                         |
                         | TCP 5432
                         v
                  postgres Service
                  ClusterIP :5432
                         |
                         v
                   PostgreSQL Pod
                         |
                         v
                  postgres-data PVC

                    backend Pod
                         |
                         v
                   upload-data PVC
```

---

# 2. Prerequisites

The following are required:

- Access to a Red Hat OpenShift cluster
- `oc` CLI installed
- Git installed
- OpenSSL installed
- Access to create projects, builds, deployments, services, PVCs, and routes

Verify the OpenShift CLI:

```bash
oc version
```

---

# 3. Login to OpenShift

From the OpenShift web console:

```text
Username -> Copy login command -> Display token
```

Run the generated login command.

Example:

```bash
oc login --token=<TOKEN> --server=<API_SERVER>
```

Verify the login:

```bash
oc whoami
```

Check cluster information:

```bash
oc cluster-info
```

List available projects:

```bash
oc projects
```

---

# 4. Clone the Application Repository

Clone the repository:

```bash
git clone https://github.com/Devops-Practice2025/python-doc-mgmt.git
```

Enter the repository:

```bash
cd python-doc-mgmt
```

Check the repository status:

```bash
git status
```

Check the current branch:

```bash
git branch --show-current
```

Inspect the repository structure:

```bash
find . -maxdepth 2 -type f | sort
```

---

# 5. Create the OpenShift Project

Create a dedicated OpenShift project:

```bash
oc new-project document-mgmt
```

If the project already exists:

```bash
oc project document-mgmt
```

Verify:

```bash
oc project
```

Expected:

```text
Using project "document-mgmt"
```

---

# 6. Create the Backend BuildConfig

Create a binary Docker build:

```bash
oc new-build \
  --name=document-mgmt-backend \
  --binary \
  --strategy=docker
```

Configure the backend Dockerfile:

```bash
oc patch bc/document-mgmt-backend \
  --type=merge \
  -p '{"spec":{"strategy":{"dockerStrategy":{"dockerfilePath":"Dockerfile.backend"}}}}'
```

Verify:

```bash
oc get bc document-mgmt-backend
```

---

# 7. Build the Backend Image

Start the backend build:

```bash
oc start-build document-mgmt-backend \
  --from-dir=. \
  --follow
```

Verify:

```bash
oc get builds
```

Expected:

```text
document-mgmt-backend-1   Complete
```

Check the ImageStream:

```bash
oc get imagestream document-mgmt-backend
```

---

# 8. Create the Frontend BuildConfig

Create the frontend binary build:

```bash
oc new-build \
  --name=document-mgmt-frontend \
  --binary \
  --strategy=docker
```

Configure the frontend Dockerfile:

```bash
oc patch bc/document-mgmt-frontend \
  --type=merge \
  -p '{"spec":{"strategy":{"dockerStrategy":{"dockerfilePath":"Dockerfile.frontend"}}}}'
```

Verify:

```bash
oc get bc document-mgmt-frontend
```

---

# 9. Build the Frontend Image

Start the frontend build:

```bash
oc start-build document-mgmt-frontend \
  --from-dir=. \
  --follow
```

Verify:

```bash
oc get builds
```

Expected:

```text
document-mgmt-backend-1    Complete
document-mgmt-frontend-1   Complete
```

Check ImageStreams:

```bash
oc get imagestreams
```

---

# 10. OpenShift Image Architecture

At this point the image build process is:

```text
Application Source
       |
       v
   BuildConfig
       |
       v
    Build Pod
       |
       v
 Container Image
       |
       v
   ImageStream
       |
       v
OpenShift Internal Registry
```

The images are stored inside the OpenShift internal registry.

---

# 11. Create a Working Copy of the Kubernetes Manifests

To avoid accidentally modifying the original repository while testing:

```bash
rm -rf /tmp/python-doc-mgmt-k8s
```

Copy the Kubernetes manifests:

```bash
cp -r k8s /tmp/python-doc-mgmt-k8s
```

Verify:

```bash
find /tmp/python-doc-mgmt-k8s -type f | sort
```

---

# 12. Configure OpenShift Internal Registry Images

Set the backend image:

```bash
BACKEND_IMAGE="image-registry.openshift-image-registry.svc:5000/document-mgmt/document-mgmt-backend:latest"
```

Set the frontend image:

```bash
FRONTEND_IMAGE="image-registry.openshift-image-registry.svc:5000/document-mgmt/document-mgmt-frontend:latest"
```

Check the current image references:

```bash
grep -R -n 'image:' /tmp/python-doc-mgmt-k8s
```

Update the backend image:

```bash
sed -i \
  "/image:.*document-mgmt-backend/c\        image: ${BACKEND_IMAGE}" \
  /tmp/python-doc-mgmt-k8s/base/workloads.yaml
```

Update the frontend image:

```bash
sed -i \
  "/image:.*document-mgmt-frontend/c\        image: ${FRONTEND_IMAGE}" \
  /tmp/python-doc-mgmt-k8s/base/workloads.yaml
```

Verify:

```bash
grep -n 'image:' /tmp/python-doc-mgmt-k8s/base/workloads.yaml
```

---

# 13. Create Application Secrets

Generate a PostgreSQL password:

```bash
POSTGRES_PASSWORD="$(openssl rand -hex 16)"
```

Generate the application secret key:

```bash
SECRET_KEY="$(openssl rand -hex 32)"
```

Copy the example Secret:

```bash
cp k8s/base/secret.example.yaml \
  /tmp/document-mgmt-secret.yaml
```

Protect the file:

```bash
chmod 600 /tmp/document-mgmt-secret.yaml
```

Inspect the Secret template:

```bash
cat /tmp/document-mgmt-secret.yaml
```

Replace the PostgreSQL password placeholder:

```bash
sed -i \
  "s/CHANGE_ME_POSTGRES_PASSWORD/${POSTGRES_PASSWORD}/g" \
  /tmp/document-mgmt-secret.yaml
```

Replace the application secret placeholder:

```bash
sed -i \
  "s/CHANGE_ME_SECRET_KEY/${SECRET_KEY}/g" \
  /tmp/document-mgmt-secret.yaml
```

Verify that no placeholders remain:

```bash
grep -n 'CHANGE_ME' /tmp/document-mgmt-secret.yaml
```

The command should return nothing.

Apply the Secret:

```bash
oc apply -f /tmp/document-mgmt-secret.yaml
```

Verify:

```bash
oc get secret
```

> **Important:** Never commit the real Secret file to Git.

---

# 14. PostgreSQL Persistent Storage

PostgreSQL requires persistent storage.

The architecture is:

```text
PostgreSQL Pod
      |
      v
Volume Mount
      |
      v
postgres-data PVC
      |
      v
PersistentVolume
      |
      v
StorageClass
```

The PVC allows PostgreSQL data to survive Pod recreation.

Check available StorageClasses:

```bash
oc get storageclass
```

---

# 15. Important PostgreSQL PGDATA Configuration

The PostgreSQL PVC is mounted at:

```text
/var/lib/postgresql/data
```

Some storage systems create a directory such as:

```text
lost+found
```

inside the filesystem.

PostgreSQL cannot initialize directly in a non-empty directory.

The error may look like:

```text
initdb: error: directory "/var/lib/postgresql/data" exists but is not empty
```

Therefore PostgreSQL should use a subdirectory.

Configure:

```text
PGDATA=/var/lib/postgresql/data/pgdata
```

The resulting filesystem becomes:

```text
/var/lib/postgresql/data
|
+-- lost+found
|
+-- pgdata
    |
    +-- base
    +-- global
    +-- pg_wal
    +-- ...
```

Add the following environment variable to the PostgreSQL container:

```yaml
- name: PGDATA
  value: /var/lib/postgresql/data/pgdata
```

---

# 16. PostgreSQL Service

PostgreSQL should be accessed through a Kubernetes Service.

The backend should connect to:

```text
postgres:5432
```

Architecture:

```text
Backend Pod
     |
     | postgres:5432
     v
Postgres Service
     |
     v
PostgreSQL Pod
```

Do not configure the backend using the PostgreSQL Pod IP.

Pod IP addresses are temporary.

The Service provides stable DNS.

---

# 17. Configure the Frontend Service

The frontend application listens on:

```text
5000
```

The Service should expose:

```text
80
```

and forward traffic to:

```text
5000
```

The clean Service configuration is:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  type: ClusterIP

  selector:
    app: frontend

  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 5000
```

Traffic flow:

```text
frontend Service
      |
      | port 80
      v
 targetPort 5000
      |
      v
frontend Pods
```

---

# 18. Why the Frontend Service Uses ClusterIP

The frontend Service should use:

```yaml
type: ClusterIP
```

It does not need:

```yaml
type: LoadBalancer
```

because OpenShift provides external access using a Route.

Correct architecture:

```text
Internet
   |
   v
OpenShift Router
   |
   v
Route
   |
   v
ClusterIP Service
   |
   v
Pods
```

---

# 19. Configure the OpenShift Route

Create or update:

```text
/tmp/python-doc-mgmt-k8s/openshift/route.yaml
```

Use:

```yaml
apiVersion: route.openshift.io/v1
kind: Route

metadata:
  name: document-mgmt

spec:

  to:
    kind: Service
    name: frontend
    weight: 100

  port:
    targetPort: http

  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect

  wildcardPolicy: None
```

The important configuration is:

```yaml
targetPort: http
```

The Route uses the named frontend Service port.

---

# 20. Route Traffic Flow

The complete external traffic flow is:

```text
Browser
   |
   | HTTPS
   v
OpenShift Router
   |
   v
Route
targetPort=http
   |
   v
frontend Service
port=80
targetPort=5000
   |
   v
frontend Pods
port=5000
```

---

# 21. TLS Edge Termination

The Route uses:

```yaml
termination: edge
```

This means:

```text
Browser
   |
   | HTTPS
   v
OpenShift Router
   |
   | TLS terminates here
   |
   | HTTP
   v
Frontend Service
   |
   v
Frontend Pod
```

The frontend application does not need to manage the external TLS certificate itself.

---

# 22. Configure Kustomize

The repository uses a base/overlay structure:

```text
k8s/
|
+-- base/
|
+-- openshift/
```

The base contains common Kubernetes resources.

The OpenShift overlay contains OpenShift-specific configuration such as the Route.

Create or verify:

```text
/tmp/python-doc-mgmt-k8s/openshift/kustomization.yaml
```

Example:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../base
  - route.yaml
```

> **Important:** Do not include HTML tags such as `<br>` inside YAML files.

---

# 23. Validate the YAML Files

Check that no accidental HTML tags exist:

```bash
grep -RIn \
  --include='*.yaml' \
  --include='*.yml' \
  '<br>' \
  /tmp/python-doc-mgmt-k8s || true
```

The command should return nothing.

---

# 24. Render the Kustomize Configuration

Render the final manifests:

```bash
oc kustomize /tmp/python-doc-mgmt-k8s/openshift \
  > /tmp/rendered.yaml
```

Verify that rendering succeeded:

```bash
test -s /tmp/rendered.yaml && \
echo "Kustomize rendering successful"
```

Inspect important resources:

```bash
grep -nE \
'^kind:|^  name:|targetPort:|PGDATA|type: ClusterIP' \
/tmp/rendered.yaml
```

---

# 25. Perform Server-Side Validation

Before creating resources, validate them against the OpenShift API server:

```bash
oc apply \
  --dry-run=server \
  -f /tmp/rendered.yaml
```

Only continue if the validation succeeds.

---

# 26. Deploy the Application

Apply the rendered manifests:

```bash
oc apply -f /tmp/rendered.yaml
```

Alternatively:

```bash
oc apply -k /tmp/python-doc-mgmt-k8s/openshift
```

---

# 27. Watch the Pods

Monitor Pod creation:

```bash
oc get pods -w
```

Eventually the application should look similar to:

```text
backend-xxxxx       1/1   Running
frontend-xxxxx      1/1   Running
frontend-yyyyy      1/1   Running
postgres-xxxxx      1/1   Running
```

Press:

```text
Ctrl+C
```

after everything becomes stable.

---

# 28. Verify Deployments

Run:

```bash
oc get deployments
```

Expected:

```text
NAME       READY   UP-TO-DATE   AVAILABLE
backend    1/1     1            1
frontend   2/2     2            2
postgres   1/1     1            1
```

---

# 29. Verify Services

Run:

```bash
oc get svc
```

Expected architecture:

```text
backend     ClusterIP   ...   8000/TCP
frontend    ClusterIP   ...   80/TCP
postgres    ClusterIP   ...   5432/TCP
```

---

# 30. Verify Persistent Storage

Run:

```bash
oc get pvc
```

Expected:

```text
postgres-data   Bound   5Gi   RWO
upload-data     Bound   5Gi   RWO
```

The important concept is:

```text
Pod deleted
     |
     v
New Pod created
     |
     v
Same PVC attached
     |
     v
Data survives
```

---

# 31. Verify PostgreSQL

Check the PostgreSQL Pod:

```bash
oc get pods -l app=postgres
```

Check PostgreSQL logs:

```bash
oc logs deployment/postgres --tail=100
```

Successful startup should contain:

```text
database system is ready to accept connections
```

Verify `PGDATA`:

```bash
oc set env deployment/postgres --list | grep PGDATA
```

Expected:

```text
PGDATA=/var/lib/postgresql/data/pgdata
```

Check PostgreSQL readiness:

```bash
oc exec deployment/postgres -- pg_isready
```

Expected:

```text
accepting connections
```

---

# 32. Verify the Backend

Check the backend Pod:

```bash
oc get pods -l app=backend
```

Check backend logs:

```bash
oc logs deployment/backend --tail=100
```

Check Deployment status:

```bash
oc get deployment backend
```

---

# 33. Verify Backend-to-PostgreSQL Connectivity

Test TCP connectivity from the backend to PostgreSQL:

```bash
oc exec -i deployment/backend -- python - <<'PY'
import socket

with socket.create_connection(("postgres", 5432), timeout=5):
    print("backend -> postgres:5432 OK")
PY
```

Expected:

```text
backend -> postgres:5432 OK
```

This demonstrates Kubernetes DNS-based Service discovery:

```text
Backend
   |
   | postgres:5432
   v
Postgres Service
   |
   v
PostgreSQL Pod
```

---

# 34. Verify the Frontend

Check frontend Pods:

```bash
oc get pods -l app=frontend
```

Expected:

```text
frontend-xxxxx   1/1   Running
frontend-yyyyy   1/1   Running
```

Check frontend logs:

```bash
oc logs deployment/frontend --tail=50
```

Successful health checks should look similar to:

```text
GET /healthz HTTP/1.1 200
```

---

# 35. Verify the Frontend Service

Check the Service:

```bash
oc get svc frontend
```

Inspect it:

```bash
oc get svc frontend -o yaml
```

The important configuration should be:

```yaml
type: ClusterIP

ports:
  - name: http
    port: 80
    targetPort: 5000
```

---

# 36. Verify Frontend Endpoints

Run:

```bash
oc get endpoints frontend
```

You should see frontend Pod endpoints similar to:

```text
10.x.x.x:5000,10.x.x.x:5000
```

This means:

```text
frontend Service
       |
       v
EndpointSlice
       |
       +---- frontend Pod 1 :5000
       |
       +---- frontend Pod 2 :5000
```

---

# 37. Verify EndpointSlices

Run:

```bash
oc get endpointslice \
  -l kubernetes.io/service-name=frontend
```

For more detail:

```bash
oc get endpointslice \
  -l kubernetes.io/service-name=frontend \
  -o yaml
```

EndpointSlices contain the actual Pod endpoints used by the Service.

---

# 38. Verify the OpenShift Route

Run:

```bash
oc get route
```

Expected:

```text
document-mgmt
```

Inspect the Route:

```bash
oc get route document-mgmt -o yaml
```

Check Route admission:

```bash
oc get route document-mgmt \
  -o jsonpath='{range .status.ingress[*]}host={.host}{" "}{range .conditions[*]}{.type}={.status}{"\n"}{end}{end}'
```

Expected:

```text
Admitted=True
```

---

# 39. Get the Application URL

Run:

```bash
ROUTE_HOST="$(oc get route document-mgmt \
  -o jsonpath='{.spec.host}')"
```

Display the URL:

```bash
echo "https://${ROUTE_HOST}"
```

Example:

```text
https://document-mgmt-document-mgmt.apps.<cluster>.dyn.redhatworkshops.io
```

---

# 40. Test the Application Health Endpoint

Run:

```bash
curl -k \
  "https://${ROUTE_HOST}/healthz"
```

Or:

```bash
curl -sk \
  -o /dev/null \
  -w 'HTTP %{http_code}\n' \
  "https://${ROUTE_HOST}/healthz"
```

Expected:

```text
HTTP 200
```

---

# 41. Open the Application

Open the following URL in a browser:

```text
https://<ROUTE_HOST>
```

The application should now be accessible externally through the OpenShift Route.

---

# 42. Complete Deployment Verification

Run:

```bash
echo "===== PROJECT ====="
oc project

echo "===== BUILDS ====="
oc get builds

echo "===== IMAGESTREAMS ====="
oc get imagestreams

echo "===== PODS ====="
oc get pods

echo "===== DEPLOYMENTS ====="
oc get deployments

echo "===== SERVICES ====="
oc get svc

echo "===== PVC ====="
oc get pvc

echo "===== ROUTE ====="
oc get route

echo "===== ENDPOINTS ====="
oc get endpoints

echo "===== ENDPOINT SLICES ====="
oc get endpointslice

echo "===== EVENTS ====="
oc get events --sort-by='.lastTimestamp' | tail -20
```

---

# 43. Expected Healthy State

Pods:

```text
backend-xxxxx       1/1   Running
frontend-xxxxx      1/1   Running
frontend-yyyyy      1/1   Running
postgres-xxxxx      1/1   Running
```

Deployments:

```text
backend    1/1
frontend   2/2
postgres   1/1
```

PVCs:

```text
postgres-data   Bound
upload-data     Bound
```

Services:

```text
backend     ClusterIP
frontend    ClusterIP
postgres    ClusterIP
```

Route:

```text
document-mgmt   Admitted=True
```

Application health:

```text
HTTP 200
```

---

# 44. OpenShift Concepts Used in This Project

| Concept | Usage |
|---|---|
| Project | `document-mgmt` |
| Namespace | Application isolation |
| Pod | Runs application containers |
| Deployment | Manages application Pods |
| ReplicaSet | Maintains desired Pod replicas |
| Labels | Identifies application Pods |
| Selectors | Connects Services to Pods |
| Service | Stable internal networking |
| ClusterIP | Internal Service exposure |
| DNS | `frontend`, `backend`, `postgres` |
| containerPort | Container listening port |
| Service port | Stable Service-facing port |
| targetPort | Destination container port |
| EndpointSlice | Actual Pod endpoints |
| Route | External OpenShift access |
| OpenShift Router | Routes external traffic |
| Edge TLS | TLS termination at router |
| Readiness Probe | Determines traffic eligibility |
| Liveness Probe | Detects unhealthy containers |
| PVC | Requests persistent storage |
| PV | Provides persistent storage |
| StorageClass | Dynamic storage provisioning |
| RWO | ReadWriteOnce storage mode |
| Secret | Sensitive configuration |
| Environment Variable | Runtime configuration |
| BuildConfig | OpenShift image build definition |
| Build Pod | Builds container images |
| ImageStream | OpenShift image management |
| Internal Registry | Stores application images |
| Kustomize | Base and OpenShift overlays |

---

# 45. Important OpenShift Concepts

## Project

An OpenShift Project provides isolation for application resources.

```text
document-mgmt
|
+-- Deployments
+-- Pods
+-- Services
+-- Routes
+-- Secrets
+-- PVCs
+-- Builds
+-- ImageStreams
```

---

## Deployment

A Deployment manages application Pods.

```text
Deployment
    |
    v
ReplicaSet
    |
    v
Pods
```

If a Pod fails, the Deployment creates another Pod.

---

## Service

Pods are temporary and their IP addresses can change.

A Service provides a stable network identity.

Instead of:

```text
backend -> 10.132.0.100:5432
```

use:

```text
backend -> postgres:5432
```

---

## Labels and Selectors

Frontend Pods have a label such as:

```yaml
app: frontend
```

The frontend Service uses:

```yaml
selector:
  app: frontend
```

This creates:

```text
Service
   |
   | selector app=frontend
   v
Frontend Pods
```

---

## Service Port and TargetPort

The frontend container listens on:

```text
5000
```

The Service exposes:

```text
80
```

Therefore:

```text
Service :80
     |
     v
targetPort :5000
     |
     v
Frontend Container :5000
```

---

## EndpointSlice

The Service does not directly contain Pod IP addresses.

Kubernetes maintains EndpointSlices containing the actual backend endpoints.

Example:

```text
frontend Service
       |
       v
EndpointSlice
       |
       +---- 10.x.x.x:5000
       |
       +---- 10.x.x.x:5000
```

---

## Route

OpenShift Route provides external access to the application.

```text
Internet
   |
   v
OpenShift Router
   |
   v
Route
   |
   v
Service
   |
   v
Pods
```

---

## Edge TLS Termination

With:

```yaml
termination: edge
```

TLS terminates at the OpenShift Router.

```text
Browser
   |
 HTTPS
   |
   v
OpenShift Router
   |
 HTTP
   |
   v
Frontend
```

---

## PersistentVolumeClaim

Pods are disposable.

Persistent data should therefore be stored outside the Pod filesystem.

```text
PostgreSQL Pod
      |
      v
     PVC
      |
      v
     PV
      |
      v
Storage Backend
```

---

## ReadWriteOnce

The PVC uses:

```text
RWO
```

which means:

```text
ReadWriteOnce
```

The volume can be mounted read/write according to the storage provider's RWO semantics.

This is important when designing application replica counts around persistent storage.

---

## Secret

Sensitive values should not be stored directly in source code.

Use:

```text
Secret
   |
   v
Environment Variables
   |
   v
Application
```

Examples include:

- PostgreSQL password
- Application secret key

---

## Readiness Probe

A readiness probe answers:

> Is this Pod ready to receive traffic?

Example:

```text
GET /healthz
```

If it returns:

```text
HTTP 200
```

the Pod is considered ready.

If readiness fails, the Pod is removed from Service traffic until it becomes ready again.

---

## Liveness Probe

A liveness probe answers:

> Is this application still healthy?

If the liveness probe repeatedly fails, Kubernetes can restart the container.

---

## BuildConfig

OpenShift can build container images inside the cluster.

```text
Source Code
    |
    v
BuildConfig
    |
    v
Build Pod
    |
    v
Container Image
    |
    v
ImageStream
```

---

## ImageStream

An ImageStream provides OpenShift-native image management.

The application Deployment can consume images stored in the OpenShift internal registry.

---

## Kustomize

Kustomize allows common Kubernetes resources to be maintained separately from environment-specific configuration.

Example:

```text
k8s/
|
+-- base/
|   |
|   +-- deployments
|   +-- services
|   +-- PVCs
|
+-- openshift/
    |
    +-- route.yaml
    +-- kustomization.yaml
```

The final configuration can be rendered using:

```bash
oc kustomize k8s/openshift
```

and deployed using:

```bash
oc apply -k k8s/openshift
```

---

# 46. Important Lessons Learned

## Lesson 1 — Never Depend on Pod IP Addresses

Wrong:

```text
backend -> 10.132.0.100:5432
```

Correct:

```text
backend -> postgres:5432
```

Use Kubernetes Services and DNS.

---

## Lesson 2 — Pods Are Disposable

```text
Deployment
    |
    v
ReplicaSet
    |
    v
Pod
```

If a Pod disappears, Kubernetes creates another one.

---

## Lesson 3 — Persistent Data Must Not Live Only Inside Pods

```text
PostgreSQL Pod
      |
      v
     PVC
      |
      v
     PV
```

The Pod can disappear while the database data survives.

---

## Lesson 4 — Service Port and Container Port Can Differ

Frontend:

```text
Service :80
     |
     v
targetPort :5000
     |
     v
Frontend Container :5000
```

---

## Lesson 5 — Use ClusterIP Behind an OpenShift Route

Correct:

```text
Internet
   |
   v
Route
   |
   v
ClusterIP Service
   |
   v
Pods
```

A separate `LoadBalancer` Service is unnecessary for this architecture.

---

## Lesson 6 — Use Named Ports With Routes

Prefer:

```yaml
ports:
  - name: http
    port: 80
    targetPort: 5000
```

and:

```yaml
port:
  targetPort: http
```

This makes the Route-to-Service relationship explicit.

---

## Lesson 7 — PostgreSQL Needs a Clean PGDATA Directory

With mounted storage:

```text
/var/lib/postgresql/data
|
+-- lost+found
|
+-- pgdata
```

Use:

```text
PGDATA=/var/lib/postgresql/data/pgdata
```

---

## Lesson 8 — Health Probes Are Important

```text
OpenShift
    |
    v
GET /healthz
    |
    +---- HTTP 200 -> Ready
    |
    +---- Failure -> Remove from Service traffic
```

---

## Lesson 9 — Verify Before Changing Resources

Useful verification commands include:

```bash
oc get pods
oc get deployments
oc get svc
oc get endpoints
oc get endpointslice
oc get pvc
oc get route
oc get events
```

Always inspect the current state before making destructive changes.

---

## Lesson 10 — Preserve Persistent Storage During Troubleshooting

Avoid deleting PVCs unless data destruction is explicitly intended.

For PostgreSQL:

```text
Deployment/Pod
     |
     | can be recreated
     v
PVC
     |
     | preserve
     v
Database Data
```

---

# 47. Troubleshooting Commands

## Pods

List Pods:

```bash
oc get pods
```

Describe a Pod:

```bash
oc describe pod <pod-name>
```

View logs:

```bash
oc logs <pod-name>
```

View previous container logs:

```bash
oc logs <pod-name> --previous
```

---

## Deployments

List Deployments:

```bash
oc get deployments
```

Describe the frontend Deployment:

```bash
oc describe deployment frontend
```

Restart a Deployment:

```bash
oc rollout restart deployment/frontend
```

Watch rollout:

```bash
oc rollout status deployment/frontend
```

---

## Services

List Services:

```bash
oc get svc
```

Describe the frontend Service:

```bash
oc describe svc frontend
```

View YAML:

```bash
oc get svc frontend -o yaml
```

---

## Endpoints

List endpoints:

```bash
oc get endpoints
```

Check frontend endpoints:

```bash
oc get endpoints frontend
```

---

## EndpointSlices

```bash
oc get endpointslice
```

Frontend only:

```bash
oc get endpointslice \
  -l kubernetes.io/service-name=frontend
```

---

## Persistent Storage

List PVCs:

```bash
oc get pvc
```

Describe PostgreSQL PVC:

```bash
oc describe pvc postgres-data
```

---

## Routes

List Routes:

```bash
oc get route
```

Describe the application Route:

```bash
oc describe route document-mgmt
```

View Route YAML:

```bash
oc get route document-mgmt -o yaml
```

---

## Events

View recent events:

```bash
oc get events \
  --sort-by='.lastTimestamp'
```

Last 30 events:

```bash
oc get events \
  --sort-by='.lastTimestamp' | tail -30
```

---

# 48. Troubleshooting Mental Model

When the application is unavailable, troubleshoot layer by layer.

```text
Browser
   |
   v
DNS / TLS
   |
   v
OpenShift Router
   |
   v
Route
   |
   v
Service
   |
   v
EndpointSlice
   |
   v
Pod
   |
   v
Application Process
```

Check each layer independently.

---

# 49. Application Networking Mental Model

```text
Internet
    |
    v
OpenShift Router
    |
    v
Route
    |
    v
Frontend Service
    |
    v
Frontend Pods
    |
    v
Backend Service
    |
    v
Backend Pod
    |
    v
Postgres Service
    |
    v
PostgreSQL Pod
```

---

# 50. Application Storage Mental Model

```text
PostgreSQL Pod
      |
      v
postgres-data PVC
      |
      v
PersistentVolume
      |
      v
StorageClass
      |
      v
Storage Backend
```

For uploaded documents:

```text
Backend Pod
     |
     v
upload-data PVC
     |
     v
PersistentVolume
```

---

# 51. Application Configuration Mental Model

```text
Secret / ConfigMap
        |
        v
Environment Variables
        |
        v
Application Container
```

---

# 52. OpenShift Build Mental Model

```text
Git Source
    |
    v
BuildConfig
    |
    v
Build Pod
    |
    v
Container Image
    |
    v
ImageStream
    |
    v
OpenShift Internal Registry
    |
    v
Deployment
```

---

# 53. Kubernetes Deployment Mental Model

```text
Deployment
    |
    v
ReplicaSet
    |
    v
Pods
```

---

# 54. Complete Application Mental Model

```text
                         Internet
                            |
                            v
                    OpenShift Router
                            |
                            v
                         Route
                            |
                            v
                    Frontend Service
                            |
                 +----------+----------+
                 |                     |
                 v                     v
           Frontend Pod          Frontend Pod
                 |
                 v
                    Backend Service
                            |
                            v
                       Backend Pod
                       /         \
                      /           \
                     v             v
             Postgres Service   upload-data PVC
                     |
                     v
               PostgreSQL Pod
                     |
                     v
              postgres-data PVC
```

---

# 55. Successful Deployment Checklist

Use this checklist whenever redeploying the application.

```text
[ ] 1. Install/verify oc CLI
[ ] 2. Login to OpenShift
[ ] 3. Clone python-doc-mgmt repository
[ ] 4. Create/select document-mgmt project
[ ] 5. Create backend BuildConfig
[ ] 6. Build backend image
[ ] 7. Create frontend BuildConfig
[ ] 8. Build frontend image
[ ] 9. Verify builds are Complete
[ ] 10. Verify ImageStreams
[ ] 11. Prepare Kubernetes/OpenShift manifests
[ ] 12. Configure internal registry image references
[ ] 13. Generate application secrets
[ ] 14. Create Kubernetes Secret
[ ] 15. Configure PostgreSQL PGDATA
[ ] 16. Verify PostgreSQL PVC configuration
[ ] 17. Verify upload-data PVC configuration
[ ] 18. Configure frontend Service as ClusterIP
[ ] 19. Configure frontend Service port 80 -> targetPort 5000
[ ] 20. Name frontend Service port "http"
[ ] 21. Configure OpenShift Route
[ ] 22. Configure Route targetPort as "http"
[ ] 23. Configure edge TLS termination
[ ] 24. Validate Kustomize YAML
[ ] 25. Check for accidental <br> tags
[ ] 26. Render manifests with oc kustomize
[ ] 27. Run server-side dry-run
[ ] 28. Apply manifests
[ ] 29. Verify PostgreSQL Pod
[ ] 30. Verify backend Pod
[ ] 31. Verify frontend Pods
[ ] 32. Verify Deployments
[ ] 33. Verify PVCs are Bound
[ ] 34. Verify Services
[ ] 35. Verify EndpointSlices
[ ] 36. Verify backend -> PostgreSQL connectivity
[ ] 37. Verify PostgreSQL readiness
[ ] 38. Verify frontend /healthz
[ ] 39. Verify Route admission
[ ] 40. Test HTTPS Route
[ ] 41. Open application in browser
```

---

# 56. Deployment Is Successful When

The deployment can be considered successful when all of the following conditions are true.

## Pods

```text
backend      -> Running / Ready
frontend     -> Running / Ready
frontend     -> Running / Ready
postgres     -> Running / Ready
```

## Deployments

```text
backend      -> Available
frontend     -> Available
postgres     -> Available
```

## Storage

```text
postgres-data -> Bound
upload-data   -> Bound
```

## PostgreSQL

```text
database system is ready to accept connections
```

## Backend Connectivity

```text
backend -> postgres:5432 OK
```

## Frontend Service

```text
ClusterIP
port 80
targetPort 5000
```

## Route

```text
Admitted=True
```

## Health Check

```text
HTTPS /healthz -> HTTP 200
```

## Browser

```text
Application accessible through the OpenShift Route
```

---

# 57. Quick Verification Script

After deployment, the following commands provide a quick health overview:

```bash
echo "===== PROJECT ====="
oc project

echo
echo "===== BUILDS ====="
oc get builds

echo
echo "===== IMAGESTREAMS ====="
oc get imagestreams

echo
echo "===== DEPLOYMENTS ====="
oc get deployments

echo
echo "===== PODS ====="
oc get pods -o wide

echo
echo "===== SERVICES ====="
oc get svc

echo
echo "===== ENDPOINTS ====="
oc get endpoints

echo
echo "===== ENDPOINT SLICES ====="
oc get endpointslice

echo
echo "===== PVC ====="
oc get pvc

echo
echo "===== ROUTE ====="
oc get route

echo
echo "===== POSTGRES ====="
oc exec deployment/postgres -- pg_isready

echo
echo "===== ROUTE HEALTH ====="
ROUTE_HOST="$(oc get route document-mgmt -o jsonpath='{.spec.host}')"

echo "Application URL: https://${ROUTE_HOST}"

curl -sk \
  -o /dev/null \
  -w 'HTTP %{http_code}\n' \
  "https://${ROUTE_HOST}/healthz"

echo
echo "===== RECENT EVENTS ====="
oc get events --sort-by='.lastTimestamp' | tail -20
```

---

# 58. Final Summary

This project demonstrates a complete OpenShift application deployment involving:

```text
Git
 |
 v
OpenShift BuildConfig
 |
 v
Build Pod
 |
 v
ImageStream
 |
 v
Internal Registry
 |
 v
Deployment
 |
 v
ReplicaSet
 |
 v
Pods
 |
 +----------------------+
 |                      |
 v                      v
Services              PVCs
 |                      |
 v                      v
EndpointSlices         PVs
 |
 v
OpenShift Route
 |
 v
Internet
```

The final application architecture is:

```text
Internet
   |
   v
OpenShift Route
   |
   v
Frontend Service
   |
   +----------------+
   |                |
   v                v
Frontend Pod    Frontend Pod
       |
       v
Backend Service
       |
       v
Backend Pod
   |       |
   |       +-------> upload-data PVC
   |
   v
Postgres Service
   |
   v
PostgreSQL Pod
   |
   v
postgres-data PVC
```

This deployment provides practical experience with:

- OpenShift Projects
- Kubernetes Namespaces
- BuildConfigs
- Build Pods
- ImageStreams
- OpenShift internal registry
- Deployments
- ReplicaSets
- Pods
- Labels
- Selectors
- Services
- ClusterIP networking
- Kubernetes DNS
- Service ports
- Target ports
- EndpointSlices
- OpenShift Routes
- OpenShift Router
- TLS edge termination
- Readiness probes
- Liveness probes
- Secrets
- Environment variables
- PersistentVolumeClaims
- PersistentVolumes
- StorageClasses
- ReadWriteOnce storage
- PostgreSQL persistent storage
- Kustomize
- Application health verification
- Layer-by-layer OpenShift troubleshooting

The most important request-flow model to remember is:

```text
Internet
   |
   v
Route
   |
   v
Service
   |
   v
EndpointSlice
   |
   v
Pod
   |
   v
Application
```

And the most important workload model is:

```text
Deployment
   |
   v
ReplicaSet
   |
   v
Pod
```

And the most important persistent-storage model is:

```text
Pod
 |
 v
PVC
 |
 v
PV
 |
 v
Storage Backend
```

These three mental models cover a large part of the Kubernetes/OpenShift concepts demonstrated by the `python-doc-mgmt` deployment.
