# docker installation steps:
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker

# set env variable to random values and save to .env

POSTGRES_PASSWORD=$(openssl rand -hex 16)
SECRET_KEY=$(openssl rand -hex 32)

cat > .env <<EOF
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
SECRET_KEY=${SECRET_KEY}
EOF
chmod 600 .env
ls -la .env

# Corrected Document Management Lab

Flask frontend -> FastAPI backend -> PostgreSQL metadata + persistent upload storage.

## Local run
1. Copy `.env.example` to `.env` and replace both secrets.
2. Run `docker compose up --build`.
3. Open `http://localhost:5000`.

## Build and push images
Replace `REGISTRY` and `TAG` with your ECR, Quay, or Artifact Registry values.
```bash
docker build -f Dockerfile.backend -t REGISTRY/document-mgmt-backend:TAG .
docker build -f Dockerfile.frontend -t REGISTRY/document-mgmt-frontend:TAG .
docker push REGISTRY/document-mgmt-backend:TAG
docker push REGISTRY/document-mgmt-frontend:TAG
```
Update the two image fields in `k8s/base/workloads.yaml`.

## Kubernetes: EKS or GKE
Copy `k8s/base/secret.example.yaml` to a private file, replace values, and never commit it.
```bash
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f your-private-secret.yaml
kubectl apply -k k8s/base
kubectl get pods,svc,pvc -n document-mgmt
```
The PVCs use the cluster's default StorageClass. Confirm it before deployment. The backend intentionally has one replica because the sample uses a ReadWriteOnce upload volume.

## OpenShift
Build images that your cluster can pull, update image fields, then:
```bash
oc apply -f k8s/base/namespace.yaml
oc apply -f your-private-secret.yaml
oc apply -k k8s/openshift
oc get route -n document-mgmt
```
Images are prepared for non-root execution and group-writable paths. Do not grant privileged SCC merely to bypass permissions.

## Important learning limitation
This is a lab architecture. For a scalable production version, use managed PostgreSQL and object storage (S3 or Cloud Storage), add authentication/authorization, CSRF protection, malware scanning, migrations, backups, TLS, network policies, observability, and automated tests.
