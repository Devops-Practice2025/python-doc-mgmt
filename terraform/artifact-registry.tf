resource "google_artifact_registry_repository" "application" {
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_repository
  description   = "Container images for python-doc-mgmt"
  format        = "DOCKER"

  depends_on = [
    google_project_service.required
  ]
}
