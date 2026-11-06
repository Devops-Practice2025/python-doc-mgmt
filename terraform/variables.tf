variable "project_id" {
  description = "Temporary GCP sandbox project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west1"
}

variable "artifact_repository" {
  description = "Artifact Registry Docker repository"
  type        = string
  default     = "python-doc-mgmt"
}

variable "github_service_account_id" {
  description = "Service account used by GitHub Actions"
  type        = string
  default     = "github-actions"
}
