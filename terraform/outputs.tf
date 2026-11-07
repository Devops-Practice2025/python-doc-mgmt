output "project_id" {
  value = var.project_id
}

output "region" {
  value = var.region
}

output "artifact_repository" {
  value = google_artifact_registry_repository.application.repository_id
}

output "artifact_registry_hostname" {
  value = "${var.region}-docker.pkg.dev"
}

output "artifact_registry_path" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.application.repository_id}"
}

output "github_service_account_email" {
  value = google_service_account.github_actions.email
}

output "cloud_run_runtime_service_account" {
  description = "Runtime service account used by Cloud Run"
  value       = google_service_account.cloud_run_runtime.email
}