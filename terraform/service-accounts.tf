resource "google_service_account" "github_actions" {
  project      = var.project_id
  account_id   = var.github_service_account_id
  display_name = "GitHub Actions for python-doc-mgmt"
  description  = "Builds and pushes application images to Artifact Registry"

  depends_on = [
    google_project_service.required
  ]
}

resource "google_service_account" "cloud_run_runtime" {
  project      = var.project_id
  account_id   = "python-doc-runtime"
  display_name = "python Document Management Cloud Run Runtime"
  description  = "Runtime identity for frontend and backend Cloud Run services"

  depends_on = [
    google_project_service.required
  ]
}
