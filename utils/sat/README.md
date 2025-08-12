# Security Analysis Tool (SAT) Installation Guide

This guide provides step-by-step instructions for installing and setting up the Security Analysis Tool (SAT) for Databricks WAF (Well-Architected Framework) assessment.

## Overview

The Security Analysis Tool helps assess and validate security configurations in Databricks environments. This setup consists of three main notebooks that handle service principal creation, repository cloning, and deployment validation.

## Prerequisites

- Databricks workspace with admin access
- Account-level access to Databricks
- Single-node cluster with DBR 16.3 or later
- Required Python packages:
  - `databricks-sdk`
  - `boto3`

## Installation Steps

### Step 1: WAF Security Setup (`1.WAFSecuritySetup.ipynb`)

This notebook sets up the necessary security components for WAF assessment.

**Purpose:**
- Creates a service principal for SAT operations
- Generates OAuth secrets for authentication
- Assigns workspace admin permissions across all workspaces
- Clones the security-analysis-tool repository

**Required Parameters:**
- `account_id`: Your Databricks account ID
- `client_id`: Service principal client ID
- `client_secret`: Service principal client secret

**Key Actions:**
1. Installs required packages (`databricks-sdk`, `boto3`)
2. Creates a new service principal with display name format `sdk-{timestamp}`
3. Generates OAuth secrets for the service principal
4. Assigns admin permissions to all workspaces in the account
5. Clones the SAT repository from GitHub (branch: `databricks-cluster-version`)

**Important Output:**
- Service Principal ID (printed at the end) - save this for validation

### Step 2: Clone Repository and Install (`2.clone_repo_and_install.ipynb`)

This notebook handles the repository setup and installation process.

**Requirements:**
- Must use a Single-node cluster with DBR 16.3

**Process:**
1. Clones the security-analysis-tool repository to your workspace
2. Repository URL: `https://github.com/databricks-industry-solutions/security-analysis-tool.git`
3. Switches to branch: `databricks-cluster-version`

**Manual Installation Steps:**
After running the notebook:
1. Open the cluster's Web Terminal (Cluster > Web Terminal)
2. Navigate to the security-analysis-tool directory:
   ```bash
   cd security-analysis-tool
   ```
3. Run the installation script:
   ```bash
   ./install.sh
   ```

**Cleanup:**
- The notebook includes a cleanup cell to delete the repository when needed

### Step 3: Validate Deployment (`3.waf_validate_deployment.ipynb`)

This notebook validates that the SAT deployment was successful.

**Required Parameters:**
- `account_id`: Your Databricks account ID
- `client_id`: Service principal client ID
- `client_secret`: Service principal client secret
- `sp_id`: Service Principal ID from Step 1

**Validation Checks:**
1. **Account-level permissions**: Verifies the service principal has account admin role
2. **Workspace-level permissions**: Confirms the service principal is in the workspace admins group
3. **Dashboard existence**: Checks for the SAT dashboard named "[SAT] Security Analysis Tool - Assessment Results"

**Success Indicators:**
- ✅ Green messages indicate successful validation
- ❌ Red messages indicate validation failures that need attention

## Troubleshooting

### Common Issues and Solutions

1. **Package installation failures**
   - Ensure you have network connectivity
   - Try restarting the Python kernel after package installation

2. **Permission errors**
   - Verify you have account admin privileges
   - Check that the service principal was created successfully in Step 1

3. **Repository cloning issues**
   - Ensure the workspace path doesn't conflict with existing repositories
   - Check network access to GitHub

4. **Dashboard not found**
   - The SAT dashboard is created after running the install.sh script
   - Ensure the installation script completed successfully
   - Wait a few minutes for the dashboard to appear after installation

## Security Considerations

- Store service principal credentials securely
- Rotate client secrets regularly
- Review and audit service principal permissions periodically
- Remove unnecessary workspace assignments after assessment completion

## Support

For issues or questions regarding the Security Analysis Tool, refer to the official Databricks documentation or contact your Databricks representative.

## Next Steps

After successful installation and validation:
1. Access the SAT dashboard to view assessment results
2. Review security recommendations and findings
3. Implement suggested improvements based on WAF guidelines
4. Schedule regular assessments to maintain security posture