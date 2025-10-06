# 🏗️ Oracle Cloud Infrastructure - Terraform Configuration
# Complete OKE cluster setup for AI Absence & SOW System

terraform {
  required_version = ">= 1.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

# Configure Oracle Cloud Provider
provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# Data sources
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

data "oci_core_images" "node_pool_images" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = "VM.Standard.E4.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# VCN (Virtual Cloud Network)
resource "oci_core_vcn" "ai_absence_sow_vcn" {
  compartment_id = var.compartment_ocid
  display_name   = "ai-absence-sow-vcn"
  cidr_blocks    = ["10.0.0.0/16"]
  dns_label      = "aiabsencesow"

  freeform_tags = {
    "Project"     = "AI-Absence-SOW"
    "Environment" = var.environment
    "ManagedBy"   = "Terraform"
  }
}

# Internet Gateway
resource "oci_core_internet_gateway" "ai_absence_sow_igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.ai_absence_sow_vcn.id
  display_name   = "ai-absence-sow-igw"
  enabled        = true

  freeform_tags = {
    "Project"     = "AI-Absence-SOW"
    "Environment" = var.environment
  }
}

# NAT Gateway
resource "oci_core_nat_gateway" "ai_absence_sow_nat" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.ai_absence_sow_vcn.id
  display_name   = "ai-absence-sow-nat"

  freeform_tags = {
    "Project"     = "AI-Absence-SOW"
    "Environment" = var.environment
  }
}

# Service Gateway
resource "oci_core_service_gateway" "ai_absence_sow_sg" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.ai_absence_sow_vcn.id
  display_name   = "ai-absence-sow-sg"

  services {
    service_id = data.oci_core_services.all_services.services[0].id
  }

  freeform_tags = {
    "Project"     = "AI-Absence-SOW"
    "Environment" = var.environment
  }
}

data "oci_core_services" "all_services" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}

# Route Tables
resource "oci_core_route_table" "public_route_table" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.ai_absence_sow_vcn.id
  display_name   = "public-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.ai_absence_sow_igw.id
  }

  freeform_tags = {
    "Project"     = "AI-Absence-SOW"
    "Environment" = var.environment
  }
}

resource "oci_core_route_table" "private_route_table" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.ai_absence_sow_vcn.id
  display_name   = "private-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_nat_gateway.ai_absence_sow_nat.id
  }

  route_rules {
    destination       = data.oci_core_services.all_services.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
    network_entity_id = oci_core_service_gateway.ai_absence_sow_sg.id
  }

  freeform_tags = {
    "Project"     = "AI-Absence-SOW"
    "Environment" = var.environment
  }
}

# Security Lists
resource "oci_core_security_list" "public_security_list" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.ai_absence_sow_vcn.id
  display_name   = "public-security-list"

  # Ingress Rules
  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 80
      max = 80
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "10.0.0.0/16"
    tcp_options {
      min = 22
      max = 22
    }
  }

  # Egress Rules
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }

  freeform_tags = {
    "Project"     = "AI-Absence-SOW"
    "Environment" = var.environment
  }
}

resource "oci_core_security_list" "private_security_list" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.ai_absence_sow_vcn.id
  display_name   = "private-security-list"

  # Ingress Rules - Allow all traffic from VCN
  ingress_security_rules {
    protocol = "all"
    source   = "10.0.0.0/16"
  }

  # Egress Rules
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }

  freeform_tags = {
    "Project"     = "AI-Absence-SOW"
    "Environment" = var.environment
  }
}

# Subnets
resource "oci_core_subnet" "public_subnet" {
  compartment_id      = var.compartment_ocid
  vcn_id              = oci_core_vcn.ai_absence_sow_vcn.id
  cidr_block          = "10.0.1.0/24"
  display_name        = "public-subnet"
  dns_label           = "public"
  route_table_id      = oci_core_route_table.public_route_table.id
  security_list_ids   = [oci_core_security_list.public_security_list.id]
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name

  freeform_tags = {
    "Project"     = "AI-Absence-SOW"
    "Environment" = var.environment
  }
}

resource "oci_core_subnet" "private_subnet" {
  compartment_id                 = var.compartment_ocid
  vcn_id                         = oci_core_vcn.ai_absence_sow_vcn.id
  cidr_block                     = "10.0.2.0/24"
  display_name                   = "private-subnet"
  dns_label                      = "private"
  route_table_id                 = oci_core_route_table.private_route_table.id
  security_list_ids              = [oci_core_security_list.private_security_list.id]
  availability_domain            = data.oci_identity_availability_domains.ads.availability_domains[0].name
  prohibit_public_ip_on_vnic     = true

  freeform_tags = {
    "Project"     = "AI-Absence-SOW"
    "Environment" = var.environment
  }
}

# OKE Cluster
resource "oci_containerengine_cluster" "ai_absence_sow_cluster" {
  compartment_id     = var.compartment_ocid
  kubernetes_version = var.kubernetes_version
  name               = "ai-absence-sow-cluster"
  vcn_id             = oci_core_vcn.ai_absence_sow_vcn.id

  cluster_pod_network_options {
    cni_type = "FLANNEL_OVERLAY"
  }

  endpoint_config {
    is_public_ip_enabled = true
    subnet_id            = oci_core_subnet.public_subnet.id
  }

  options {
    service_lb_subnet_ids = [oci_core_subnet.public_subnet.id]

    add_ons {
      is_kubernetes_dashboard_enabled = false
      is_tiller_enabled               = false
    }

    kubernetes_network_config {
      pods_cidr     = "10.244.0.0/16"
      services_cidr = "10.96.0.0/16"
    }
  }

  freeform_tags = {
    "Project"     = "AI-Absence-SOW"
    "Environment" = var.environment
    "ManagedBy"   = "Terraform"
  }
}

# Node Pool
resource "oci_containerengine_node_pool" "ai_absence_sow_node_pool" {
  cluster_id         = oci_containerengine_cluster.ai_absence_sow_cluster.id
  compartment_id     = var.compartment_ocid
  kubernetes_version = var.kubernetes_version
  name               = "ai-absence-sow-node-pool"

  node_config_details {
    placement_configs {
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
      subnet_id           = oci_core_subnet.private_subnet.id
    }

    size = var.node_pool_size

    node_pool_pod_network_option_details {
      cni_type          = "FLANNEL_OVERLAY"
      max_pods_per_node = 31
    }
  }

  node_shape = var.node_shape

  node_shape_config {
    memory_in_gbs = var.node_memory_in_gbs
    ocpus         = var.node_ocpus
  }

  node_source_details {
    image_id    = data.oci_core_images.node_pool_images.images[0].id
    source_type = "IMAGE"

    boot_volume_size_in_gbs = var.node_boot_volume_size_in_gbs
  }

  ssh_public_key = var.ssh_public_key

  freeform_tags = {
    "Project"     = "AI-Absence-SOW"
    "Environment" = var.environment
    "ManagedBy"   = "Terraform"
  }
}