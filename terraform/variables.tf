# 🔧 Terraform Variables for Oracle Cloud Infrastructure

# Oracle Cloud Provider Configuration
variable "tenancy_ocid" {
  description = "The OCID of the tenancy"
  type        = string
}

variable "user_ocid" {
  description = "The OCID of the user"
  type        = string
}

variable "fingerprint" {
  description = "The fingerprint of the public key"
  type        = string
}

variable "private_key_path" {
  description = "The path to the private key file"
  type        = string
}

variable "region" {
  description = "The Oracle Cloud region"
  type        = string
  default     = "us-phoenix-1"
}

variable "compartment_ocid" {
  description = "The OCID of the compartment"
  type        = string
}

# Environment Configuration
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# Kubernetes Configuration
variable "kubernetes_version" {
  description = "The version of Kubernetes to use"
  type        = string
  default     = "v1.28.2"
}

# Node Pool Configuration
variable "node_pool_size" {
  description = "The number of nodes in the node pool"
  type        = number
  default     = 3
  
  validation {
    condition     = var.node_pool_size >= 1 && var.node_pool_size <= 10
    error_message = "Node pool size must be between 1 and 10."
  }
}

variable "node_shape" {
  description = "The shape of the nodes"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "node_ocpus" {
  description = "The number of OCPUs for each node"
  type        = number
  default     = 2
  
  validation {
    condition     = var.node_ocpus >= 1 && var.node_ocpus <= 64
    error_message = "Node OCPUs must be between 1 and 64."
  }
}

variable "node_memory_in_gbs" {
  description = "The amount of memory in GBs for each node"
  type        = number
  default     = 16
  
  validation {
    condition     = var.node_memory_in_gbs >= 1 && var.node_memory_in_gbs <= 1024
    error_message = "Node memory must be between 1 and 1024 GBs."
  }
}

variable "node_boot_volume_size_in_gbs" {
  description = "The size of the boot volume in GBs for each node"
  type        = number
  default     = 100
  
  validation {
    condition     = var.node_boot_volume_size_in_gbs >= 50 && var.node_boot_volume_size_in_gbs <= 32768
    error_message = "Boot volume size must be between 50 and 32768 GBs."
  }
}

# SSH Configuration
variable "ssh_public_key" {
  description = "The SSH public key for accessing the nodes"
  type        = string
}

# Application Configuration
variable "app_name" {
  description = "The name of the application"
  type        = string
  default     = "ai-absence-sow"
}

variable "app_version" {
  description = "The version of the application"
  type        = string
  default     = "1.0.0"
}

# Database Configuration
variable "db_admin_password" {
  description = "The admin password for the database"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.db_admin_password) >= 12
    error_message = "Database password must be at least 12 characters long."
  }
}

# Load Balancer Configuration
variable "load_balancer_shape" {
  description = "The shape of the load balancer"
  type        = string
  default     = "flexible"
}

variable "load_balancer_min_bandwidth_mbps" {
  description = "The minimum bandwidth for the flexible load balancer in Mbps"
  type        = number
  default     = 10
}

variable "load_balancer_max_bandwidth_mbps" {
  description = "The maximum bandwidth for the flexible load balancer in Mbps"
  type        = number
  default     = 100
}

# Domain Configuration
variable "domain_name" {
  description = "The domain name for the application"
  type        = string
  default     = ""
}

variable "ssl_certificate_ocid" {
  description = "The OCID of the SSL certificate (optional)"
  type        = string
  default     = ""
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable monitoring and logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 30
}

# Backup Configuration
variable "enable_backups" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

# Cost Management
variable "enable_autoscaling" {
  description = "Enable cluster autoscaling"
  type        = bool
  default     = true
}

variable "min_nodes" {
  description = "Minimum number of nodes for autoscaling"
  type        = number
  default     = 1
}

variable "max_nodes" {
  description = "Maximum number of nodes for autoscaling"
  type        = number
  default     = 10
}

# Security Configuration
variable "enable_pod_security_policy" {
  description = "Enable Pod Security Policy"
  type        = bool
  default     = true
}

variable "enable_network_policy" {
  description = "Enable Network Policy"
  type        = bool
  default     = true
}

# Tags
variable "freeform_tags" {
  description = "Free-form tags to apply to all resources"
  type        = map(string)
  default = {
    "Project"     = "AI-Absence-SOW"
    "ManagedBy"   = "Terraform"
    "Owner"       = "DevOps-Team"
  }
}