Skip to main content
Databricks Logo
Get started
Developers
Reference
Release notes
Resources

English
AWS
Try Databricks
Databricks on AWS
What is Databricks?

Get started
Sign up for Databricks

Get started tutorials

Workspace UI

Data guides

Data management
Data engineering

OLTP databases (Lakebase)

Data warehousing

Data sharing

AI & analytics
AI and machine learning

Business intelligence

Platform
Architecture

Compute

Apps

Notebooks

Tables

Apache Spark

Integrations
Developers

Technology partners

Governance
Administration

Administration overview
Account administration

Workspace deployment

Manage workspace settings

Identity management

Compute policies

Audit logs

System tables

Audit log system table reference
Lineage system tables reference
Billable usage system table reference
Pricing system table reference
Compute system tables reference
Warehouses system table reference
Warehouse events system table reference
Jobs system table reference
Query history system table reference
Marketplace system tables reference
Predictive optimization system table reference
Databricks Assistant system table reference and example
Clean room events system table reference
Network access events system table reference
Shared materialization history system table reference
Workspaces system table reference
MLflow system tables reference
Data classification system tables reference
Data quality monitoring system tables reference
Zerobus system tables reference
Cost management

Security and compliance

Data governance (Unity Catalog)

Reference & resources
Reference

Release notes

Resources

AdministrationSystem tables
Last updated on Dec 18, 2025
Monitor account activity with system tables
This article explains the concept of system tables in Databricks and highlights resources you can use to get the most out of your system tables data.

What are system tables?
System tables are a Databricks-hosted analytical store of your account's operational data found in the system catalog. System tables can be used for historical observability across your account.

note
The information schema tables (system.information_schema) work differently from other system tables. See Information schema.

Requirements
To access system tables, your workspace must be enabled for Unity Catalog. For more information, see Enable system tables.
Only a subset of system tables are available in Databricks on AWS GovCloud. See Supported system tables.
Which system tables are available?
Currently, Databricks hosts the following system tables:

Table

Description

Supports streaming

Free retention period

Includes global or regional data

Audit logs (Public Preview)

Includes records for all audit events from workspaces in your region. For a list of available audit events, see Audit log reference.

Table path: system.access.audit

Yes

365 days

Regional for workspace-level events. Global for account-level events.

Billable usage

Includes records for all billable usage across your account.

Table path: system.billing.usage

Yes

365 days

Global

Clean room events (Public Preview)

Captures events related to clean rooms.

Table path: system.access.clean_room_events

Yes

365 days

Regional

Clusters

A slow-changing dimension table that contains the full history of compute configurations over time for any cluster.

Yes

365 days

Regional

Column lineage

Includes a record for each read or write event on a Unity Catalog column (but does not include events that do not have a source).

Table path: system.access.column_lineage

Yes

365 days

Regional

Data classification results (Beta)

Stores column-level detections of sensitive data classes across enabled catalogs in your metastore.

Table path: system.data_classification.results

No

365 days

Regional

Data quality monitoring results (Beta)

Stores results of data quality monitoring checks (freshness, completeness) and incident information, including downstream impact and root cause analysis, across enabled tables in your metastore.

Table path: system.data_quality_monitoring.table_results

No

Indefinite

Regional

Databricks Assistant events (Public Preview)

Tracks user messages sent to the Databricks Assistant.

Table path: system.access.assistant_events

No

365 days

Regional

Delta Sharing data materialization events

Captures data materialization events created from view, materialized view, and streaming table sharing.

Table path: system.sharing.materialization_history

Yes

365 days

Regional for workspace-level events.

Job run timeline

Tracks the start and end times of job runs.

Table path: system.lakeflow.job_run_timeline

Yes

365 days

Regional

Job task timeline

Tracks the start and end times and compute resources used for job task runs.

Table path: system.lakeflow.job_task_run_timeline

Yes

365 days

Regional

Job tasks

Tracks all job tasks that run in the account.

Table path: system.lakeflow.job_tasks

Yes

365 days

Regional

Jobs

Tracks all jobs created in the account.

Table path: system.lakeflow.jobs

Yes

365 days

Regional

Marketplace funnel events (Public Preview)

Includes consumer impression and funnel data for your listings.

Table path: system.marketplace.listing_funnel_events

Yes

365 days

Regional

Marketplace listing access (Public Preview)

Includes consumer info for completed request data or get data events on your listings.

Table path: system.marketplace.listing_access_events

Yes

365 days

Regional

MLflow tracking experiment metadata (Public Preview)

Each row represents an experiment created in the Databricks-managed MLflow system.

Table path: system.mlflow.experiments_latest

Yes

180 days

Regional

MLflow tracking run metadata (Public Preview)

Each row represents a run created in the Databricks-managed MLflow system.

Table path: system.mlflow.runs_latest

Yes

180 days

Regional

MLflow tracking run metrics (Public Preview)

Holds the timeseries metrics logged to MLflow associated with a given model training, evaluation, or agent development.

Table path: system.mlflow.run_metrics_history

Yes

180 days

Regional

Model serving endpoint data (Public Preview)

A slow-changing dimension table that stores metadata for each served foundation model in a model serving endpoint.

Table path: system.serving.served_entities

Yes

365 days

Regional

Model serving endpoint usage (Public Preview)

Captures token counts for each request to a model serving endpoint and its responses. To capture the endpoint usage in this table, you must enable usage tracking on your serving endpoint.

Table path: system.serving.endpoint_usage

Yes

90 days

Regional

Network access events (Inbound) (Public Preview)

A table that records an event for every time inbound access to a workspace is denied by an ingress policy.

Table path: system.access.inbound_network

Yes

30 days

Regional

Network access events (Outbound) (Public Preview)

A table that records an event every time outbound internet access is denied from your account.

Table path: system.access.outbound_network

Yes

365 days

Regional

Node timeline

Captures the utilization metrics of your all-purpose and jobs compute resources.

Table path: system.compute.node_timeline

Yes

90 days

Regional

Node types

Captures the currently available node types with their basic hardware information.

Table path: system.compute.node_types

No

Indefinite

Regional

Pipeline update timeline (Public Preview)

Tracks the start and end times and compute resources used for pipeline updates.

Table path: system.lakeflow.pipeline_update_timeline

Yes

365 days

Regional

Pipelines (Public Preview)

Tracks all pipelines created in the account.

Table path: system.lakeflow.pipelines

Yes

365 days

Regional

Predictive optimization (Public Preview)

Tracks the operation history of the predictive optimization feature.

Table path: system.storage.predictive_optimization_operations_history

No

180 days

Regional

Pricing

A historical log of SKU pricing. A record gets added each time there is a change to a SKU price.

Table path: system.billing.list_prices

No

Indefinite

Global

Query history (Public Preview)

Captures records for all queries run on SQL warehouses and serverless compute for notebooks and jobs.

Table path: system.query.history

No

365 days

Regional

SQL warehouse events (Public Preview)

Captures events related to SQL warehouses. For example, starting, stopping, running, scaling up and down.

Table path: system.compute.warehouse_events

Yes

365 days

Regional

SQL warehouses (Public Preview)

Contains the full history of configurations over time for any SQL warehouse.

Table path: system.compute.warehouses

Yes

365 days

Regional

Table lineage

Includes a record for each read or write event on a Unity Catalog table or path.

Table path: system.access.table_lineage

Yes

365 days

Regional

Workspaces (Public Preview)

The workspaces_latest table is a slow-changing dimension table of metadata for all the workspaces in the account.

Table path: system.access.workspaces_latest

No

Indefinite

Global

Zerobus Ingest (Streams) (Beta)

A table that stores all data related to stream events incurred by Zerobus Ingest usage.

Table path: system.lakeflow.zerobus_stream

Yes

365 days

Regional

Zerobus Ingest (Ingestion) (Beta)

A table that stores all data related to records ingested using Zerobus Ingest.

Table path: system.lakeflow.zerobus_ingest

Yes

365 days

Regional

The billable usage and pricing tables are free to use. Tables in Public Preview are also free to use during the preview, but could incur a charge in the future.

note
You may see other system tables in your account, in addition to the ones listed above. Those tables are currently in Private Preview and are empty by default. If you are interested in using any of these tables, please reach out to your Databricks account team.

System tables relationships
The following entity-relationship diagram outlines how the currently available system tables relate to one another. This diagram highlights the primary and foreign keys of each table.

Entity relationship diagram of the Databricks system tables

Enable system tables
Because system tables are governed by Unity Catalog, you need to have at least one Unity Catalog-enabled workspace in your account to enable your account's system tables. System tables include data from all workspaces in your account, but they can only be accessed from a Unity Catalog-enabled workspace.

The metastore needs to be on Unity Catalog Privilege Model Version 1.0 to access system tables. See Upgrade to privilege inheritance.

Grant access to system tables
Access to system tables is governed by Unity Catalog. Account admins have access to system tables by default. To allow a user to query system tables, an admin must grant that user USE and SELECT permissions on the system schemas. See Manage privileges in Unity Catalog.

System tables are read-only and cannot be modified.

note
If your account was created after November 8, 2023, you might not have a metastore admin by default. For more information, see Get started with Unity Catalog.

Do system tables contain data for all workspaces in your account?
System tables contain operational data for all workspaces in your account deployed within the same cloud region. Some tables include global data. For details, see the list of available tables.

Although system tables can only be accessed through a Unity Catalog workspace, they include operational data from non-Unity Catalog workspaces in your account.

Where is system table data stored?
Your account's system table data is stored in a Databricks-hosted storage account located in the same region as your metastore. The data is securely shared with you using Delta Sharing.

Each table has a free data retention period. For details, see the Free retention period column in Which system tables are available?.

Where are system tables located in Catalog Explorer?
The system tables in your account are located in a catalog called system, which is included in every Unity Catalog metastore. In the system catalog, you'll see schemas such as access and billing that contain the system tables.

Considerations for streaming system tables
Databricks uses Delta Sharing to share system table data with customers. Be aware of the following considerations when streaming with Delta Sharing:

If you are using streaming with system tables, set the skipChangeCommits option to true. This ensures the streaming job is not disrupted by deletes in the system tables. See Ignore updates and deletes.
Trigger.AvailableNow is not supported with Delta Sharing streaming. It will be converted to Trigger.Once.
System tables use the default 7 days retention for VACUUM (see Configure data retention for time travel queries), meaning your streaming query might break if it lags behind by more than 7 days. Monitor your streams to make sure they catch up with the latest system table version.
If you use a trigger in your streaming job and find it isn't catching up to the latest system table version, Databricks recommends increasing the scheduled frequency of the job.

Read incremental changes from streaming system tables
Python
spark.readStream.option("skipChangeCommits", "true").table("system.billing.usage")

Known issues
New columns may be added to existing system tables at any time. Queries that rely on a fixed schema may break if new columns are introduced. Existing columns will not change or be removed. If you are writing system table data to another target table, consider enabling schema evolution.
No support for real-time monitoring. Data is updated throughout the day. If you don't see a log for a recent event, check back later.
The __internal_logging system table schema supports payload logging using AI Gateway-enabled inference tables for external models and provisioned throughput workloads. This schema is visible to account admins, but it cannot be enabled and should not be used for customer workflows.
If your workspace uses a customer-managed VPC, you might be denied access to the S3 bucket where the logs are stored. If so, you need to update your VPC endpoint policy to allow access to the S3 bucket where your region's system tables data is stored. For a list of regional bucket names, see the System tables bucket column in Storage bucket addresses table.
The system schemas system.operational_data and system.lineage are deprecated and will contain empty tables.
What are system tables?
Requirements
Which system tables are available?
System tables relationships
Enable system tables
Grant access to system tables
Do system tables contain data for all workspaces in your account?
Where is system table data stored?
Where are system tables located in Catalog Explorer?
Considerations for streaming system tables
Read incremental changes from streaming system tables
Known issues
Was this page helpful?
Privacy Notice·Terms of Use·Modern Slavery Statement·California Privacy·Your Privacy Choices 
© Databricks 2026. All rights reserved. Apache, Apache Spark, Spark and the Spark logo are trademarks of the Apache Software Foundation.

Ask Assistant
Open Assistant