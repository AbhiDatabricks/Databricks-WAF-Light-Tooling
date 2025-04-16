
import streamlit as st
import pandas as pd
from databricks.sdk import AccountClient
from databricks.sdk.service import iam
import time
import boto3

def main():
    st.set_page_config(layout="wide")

    st.header("WAF Automation Tool v1.0")
    
    # Input for account details
    acct_id = st.text_input("Account ID:")
    service_principal_name = st.text_input("Service Principal Name:")
    cloud_provider = st.selectbox(
                        "Cloud Provider:",
                        ("AWS", "Azure", "GCP"))
    workspaces = st.text_input("Workspaces (Comma separated):")
    default_secret_store = get_secret_manager(cloud_provider)
    chosen_secret_store = st.selectbox(
                        "Secret Store:",
                        (default_secret_store, "Databricks Secrets"))
    
    
    if cloud_provider == "AWS":
        client_id = st.text_input("Client ID:")
        client_secret = st.text_input("Client Secret:")
        if chosen_secret_store == default_secret_store:
            secrets_manager_region = st.text_input("Secrets Manager Region:")
            secrets_manager_service_credential = st.text_input("Secrets Manager Service Credential:")
            secret_arn = st.text_input("Secret ARN:")
        elif chosen_secret_store == "Databricks Secrets":
            st.write("Coming Soon")
    elif cloud_provider == "Azure":
        st.write("Coming Soon")
    elif cloud_provider == "GCP":
        st.write("Coming Soon")

    if st.button("Begin", key="start_waf", help="Click to begin the WAF assessment", type="primary", disabled=False, use_container_width=False):
        if cloud_provider == "AWS":
            begin_aws_waf_assessment(acct_id, service_principal_name, workspaces, chosen_secret_store, default_secret_store, client_id, client_secret, secrets_manager_region, secrets_manager_service_credential, secret_arn)
        else:
            st.write("Coming soon for other clouds")

def begin_aws_waf_assessment(acct_id, service_principal_name, workspaces, chosen_secret_store, default_secret_store, client_id, client_secret, secrets_manager_region, secrets_manager_service_credential, secret_arn):
    
    st.write("Starting WAF assessment...")

    boto3_session = boto3.Session(botocore_session=dbutils.credentials.getServiceCredentialsProvider(secrets_manager_service_credential ), region_name=secrets_manager_region)
    sm = boto3_session.client('secretsmanager')

    a = AccountClient(
        host="https://accounts.cloud.databricks.com/",
        account_id= acct_id,
        client_id= client_id,
        client_secret= client_secret
    )

    sp = a.service_principals.create(
    active = True,
    display_name=f"sdk-{time.time_ns()}"
    )

    sp_oauth_secret = a.service_principal_secrets.create(sp.id)
    sp_oauth_secret_dict= sp_oauth_secret.as_dict()
    
    aws_secret_arn = secret_arn

    if aws_secret_arn == None or aws_secret_arn == "":
        try: 
            aws_secret = sm.create_secret(Name=generate_secret_name("databricks_waf"), SecretString=json.dumps(sp_oauth_secret_dict))
            aws_secret_arn = aws_secret.get("ARN")
        except Exception as error:
            print(f'Could not create the secret in AWS Secrets Manager: {error}')
            raise 
    else:
        try: sm.put_secret_value(SecretId=aws_secret_arn, SecretString=json.dumps(secrets_dict))
        except Exception as error:
            print(f'Could not update secret {aws_secret_arn} in AWS: {error}')
            raise 

    sp_id = sp.id
    all_workspaces = a.workspaces.list()
    for workspace in all_workspaces:
        update_workspace_assignment(workspace.workspace_id, sp_id)

    
def update_workspace_assignment(workspace_id, sp_id, a):
    _ = a.workspace_assignment.update(
        workspace_id=workspace_id,
        principal_id=sp_id,
        permissions=[iam.WorkspacePermission.ADMIN],
    )
def generate_secret_name(prefix):
    return f"{prefix}-{time.time_ns()}"


def get_secret_manager(cloud_provider):
    if cloud_provider == "AWS":
        return "AWS Secrets Manager"
    elif cloud_provider == "Azure":
        return "Azure Key Vault"
    elif cloud_provider == "GCP":
        return "Google Secret Manager"
    else:
        return "Unknown"



if __name__ == "__main__":
    main()
