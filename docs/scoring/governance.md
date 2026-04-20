# Data & AI Governance — Scoring Methodology

This pillar assesses how well your workspace implements Unity Catalog governance: lineage tracking, metadata quality, access controls, audit logging, and data quality monitoring.

## How scores are calculated

The WAF Reload job runs the control scoring query below against Databricks system tables and stores results in `waf_cache.waf_controls_g`. Each control receives a score (0–100). If the score meets or exceeds the threshold, the control is marked **Met**.

!!! note "Column naming difference"
    `waf_controls_g` stores the control description in a column named `description` rather than `best_practice` (which the other three pillar tables use). The scoring semantics are identical.

## Control Scoring Query

The following SQL computes scores for all Data & AI Governance controls. Run by the WAF Reload job and stored in `waf_cache.waf_controls_g`.

??? note "View SQL"
    ```sql
    WITH delta_usage AS (

      SELECT 

        COUNT(*) as total_tables,

        SUM(CASE WHEN data_source_format IN ('DELTA', 'ICEBERG', 'DELTASHARING') THEN 1 ELSE 0 END) as delta_tables

      FROM system.information_schema.tables

      WHERE table_catalog != 'hive_metastore'

        AND table_type IN ('MANAGED', 'EXTERNAL')

    ),

    lineage_usage AS (

      SELECT 

        COUNT(DISTINCT CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name)) as total_tables,

        COUNT(DISTINCT CASE WHEN tl.target_table_full_name IS NOT NULL THEN CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name) END) as lineage_tables

      FROM system.information_schema.tables t

      LEFT JOIN system.access.table_lineage tl ON CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name) = tl.target_table_full_name

      WHERE t.table_catalog != 'hive_metastore'

        AND t.table_type IN ('MANAGED', 'EXTERNAL')

    ),

    metadata_usage AS (

      SELECT 

        COUNT(*) as total_tables,

        SUM(CASE WHEN comment IS NOT NULL THEN 1 ELSE 0 END) as tables_with_comments,

        CASE WHEN EXISTS (SELECT 1 FROM system.information_schema.table_tags) 

          THEN (SELECT COUNT(*) FROM system.information_schema.tables WHERE table_catalog != 'hive_metastore' AND table_type IN ('MANAGED', 'EXTERNAL'))

          ELSE 0 

        END as tables_with_tags

      FROM system.information_schema.tables t

      WHERE table_catalog != 'hive_metastore'

        AND t.table_type IN ('MANAGED', 'EXTERNAL')

    ),

    waf_status AS (

      SELECT

        waf_id,

        principle,

        description,

        CASE 

        WHEN waf_id = 'DG-01-03' THEN (

          SELECT CASE WHEN total_tables > 0 THEN (lineage_tables * 100.0 / total_tables) ELSE 0 END FROM lineage_usage

        )

        WHEN waf_id = 'DG-01-04' THEN (

          SELECT CASE WHEN total_tables > 0 THEN (tables_with_comments * 100.0 / total_tables) ELSE 0 END FROM metadata_usage

        )

        WHEN waf_id = 'DG-01-05' THEN (

          SELECT CASE WHEN total_tables > 0 THEN (tables_with_tags * 100.0 / total_tables) ELSE 0 END FROM metadata_usage

        )

        WHEN waf_id = 'DG-02-01' THEN (

          CASE WHEN EXISTS (SELECT 1 FROM system.information_schema.row_filters) THEN 100 ELSE 0 END

        )

        WHEN waf_id = 'DG-02-02' THEN (

          CASE WHEN EXISTS (SELECT 1 FROM system.access.audit) THEN 100 ELSE 0 END

        )

        WHEN waf_id = 'DG-02-03' THEN (

          CASE WHEN EXISTS (

            SELECT 1 FROM system.information_schema.tables

            WHERE table_catalog = 'system' AND table_schema = 'marketplace' AND table_name = 'listing_access_events'

          ) THEN 100 ELSE 0 END

        )

        WHEN waf_id = 'DG-03-02' THEN (

          CASE WHEN EXISTS (

            SELECT 1 FROM system.information_schema.tables 

            WHERE table_name LIKE '%_drift_metrics' OR table_name LIKE '%_profile_metrics' 

          ) THEN 100 ELSE 0 END

        )

        WHEN waf_id = 'DG-03-03' THEN (

          SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage

        )

        ELSE 0

        END AS current_percentage,

        CASE 

        WHEN waf_id = 'DG-01-03' AND (

          SELECT CASE WHEN total_tables > 0 THEN (lineage_tables * 100.0 / total_tables) ELSE 0 END FROM lineage_usage

        ) >= 50 THEN 'Yes'

        WHEN waf_id = 'DG-01-04' AND (

          SELECT CASE WHEN total_tables > 0 THEN (tables_with_comments * 100.0 / total_tables) ELSE 0 END FROM metadata_usage

        ) >= 50 THEN 'Yes'

        WHEN waf_id = 'DG-01-05' AND EXISTS (SELECT 1 FROM system.information_schema.table_tags) THEN 'Yes'

        WHEN waf_id = 'DG-02-01' AND EXISTS (SELECT 1 FROM system.information_schema.row_filters) THEN 'Yes'

        WHEN waf_id = 'DG-02-02' AND EXISTS (SELECT 1 FROM system.access.audit) THEN 'Yes'

        WHEN waf_id = 'DG-02-03' AND EXISTS (

          SELECT 1 FROM system.information_schema.tables

          WHERE table_catalog = 'system' AND table_schema = 'marketplace' AND table_name = 'listing_access_events'

        ) THEN 'Yes'

        WHEN waf_id = 'DG-03-02' AND EXISTS (

          SELECT 1 FROM system.information_schema.tables 

          WHERE table_name LIKE '%_drift_metrics' OR table_name LIKE '%_profile_metrics' 

        ) THEN 'Yes'

        WHEN waf_id = 'DG-03-03' AND (

          SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage

        ) >= 80 THEN 'Yes'

        ELSE 'No'

        END AS implemented

      FROM (

        SELECT * FROM VALUES

        ('DG-01-03', 'Unify data and AI management', 'Track data and AI lineage'),

        ('DG-01-04', 'Unify data and AI management', 'Add comments to metadata'),

        ('DG-01-05', 'Unify data and AI management', 'Enable easy data discovery'),

        ('DG-02-01', 'Unify data and AI security', 'Centralize access control (row/column level)'),

        ('DG-02-02', 'Unify data and AI security', 'Configure audit logging'),

        ('DG-02-03', 'Unify data and AI security', 'Audit data platform events'),

        ('DG-03-02', 'Establish data quality standards', 'Use data quality tools and profiling'),

        ('DG-03-03', 'Establish data quality standards', 'Enforce standardized data formats')

        AS waf(waf_id, principle, description)

      )

    )

    SELECT

      waf_id,

      principle,

      description,

      ROUND(current_percentage, 1) as score_percentage,

      CASE 

      WHEN waf_id = 'DG-01-03' THEN 50

      WHEN waf_id = 'DG-01-04' THEN 50

      WHEN waf_id = 'DG-01-05' THEN 50

      WHEN waf_id = 'DG-02-01' THEN 100

      WHEN waf_id = 'DG-02-02' THEN 100

      WHEN waf_id = 'DG-02-03' THEN 100

      WHEN waf_id = 'DG-03-02' THEN 100

      WHEN waf_id = 'DG-03-03' THEN 80

      END as threshold_percentage,

      CASE 

      WHEN implemented = 'Yes' THEN 'Met'

      ELSE 'Not Met'

      END as threshold_met,

      implemented

    FROM waf_status

    ORDER BY principle, waf_id;
    ```

---

## Controls

### DG-01-03 — Track data and AI lineage to drive visibility of the data

| Field | Value |
|---|---|
| Principle | Unify data and AI management |
| Threshold | 50% |
| waf_cache table | `waf_controls_g` |

**What it measures**

% of managed/external UC tables with lineage entries in `system.access.table_lineage` (`target_table_full_name`).

**Recommendation if Not Met**

Enable Unity Catalog lineage and ensure workloads run on UC-managed objects so lineage is captured.

- Verify system tables are enabled: <https://docs.databricks.com/aws/en/admin/system-tables/>
- Use Catalog Explorer lineage or query lineage system tables: <https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage> and <https://docs.databricks.com/aws/en/admin/system-tables/lineage>
- Adopt a standard for writing via UC tables/views (avoid direct path writes that bypass governance).

**Detail Query**

??? note "View SQL"
    ```sql
    WITH lineage_tables AS (

      SELECT DISTINCT
        source_table_catalog,
        source_table_schema,
        source_table_name

      FROM (
        select distinct
          source_table_catalog,
          source_table_schema,
          source_table_name
        from system.access.table_lineage

        union

        select distinct
          target_table_catalog,
          target_table_catalog,
          target_table_name
        from system.access.table_lineage
      )

      WHERE source_table_catalog IS NOT NULL

    ),

    table_list AS (

      SELECT
        table_catalog,
        table_schema,
        table_name,
        table_type
      from system.information_schema.tables

    )

    SELECT
      table_list.table_type,
      COUNT(*) AS total_tables,
      SUM(
        CASE
          WHEN lineage_tables.source_table_catalog IS NULL THEN 0
          ELSE 1
        END
      ) AS lineage_tables
    FROM table_list
      LEFT JOIN lineage_tables
        ON table_list.table_catalog = lineage_tables.source_table_catalog
        AND table_list.table_schema = lineage_tables.source_table_schema
        AND table_list.table_name = lineage_tables.source_table_name
    GROUP BY table_list.table_type
    ```

---

### DG-01-04 — Add consistent descriptions to your metadata

| Field | Value |
|---|---|
| Principle | Unify data and AI management |
| Threshold | 50% |
| waf_cache table | `waf_controls_g` |

**What it measures**

% of managed/external UC tables with a non-null `COMMENT` in `system.information_schema.tables`.

**Recommendation if Not Met**

Roll out a metadata hygiene program and enforce COMMENT population for tables/views.

- Use Information Schema metadata to find missing comments and bulk-fix: <https://docs.databricks.com/aws/en/admin/system-tables/>
- Add "description required" to your onboarding/checklist and data product templates.
- Optionally enforce via CI checks (e.g., fail PR if new objects lack comments).

**Detail Query**

??? note "View SQL"
    ```sql
    SELECT *, count_comment/overall_count AS perc_comment
    FROM (
      select 'Tables' AS object_type,
        SUM(CASE WHEN comment is NOT NULL THEN 1 ELSE 0 END) AS count_comment,
        COUNT(*) AS overall_count
      FROM system.information_schema.tables 

      UNION ALL

      select 'Volumes' AS object_type,
        SUM(CASE WHEN comment is NOT NULL THEN 1 ELSE 0 END),
        count(*)
      FROM system.information_schema.volumes 

      UNION ALL

      select 'Catalogs' AS object_type,
        SUM(CASE WHEN comment is NOT NULL THEN 1 ELSE 0 END),
        count(*)
      FROM system.information_schema.catalogs 

      UNION ALL

      select 'Routines' AS object_type,
        SUM(CASE WHEN comment is NOT NULL THEN 1 ELSE 0 END),
        count(*)
      FROM system.information_schema.routines 

      UNION ALL

      select 'Schemas' AS object_type,
        SUM(CASE WHEN comment is NOT NULL THEN 1 ELSE 0 END),
        count(*)
      FROM system.information_schema.schemata 
    )
    ```

---

### DG-01-05 — Allow easy data discovery for data consumers

| Field | Value |
|---|---|
| Principle | Unify data and AI management |
| Threshold | 50% |
| waf_cache table | `waf_controls_g` |

**What it measures**

% of managed/external UC tables with tags present (checks existence of `system.information_schema.table_tags`; score uses % tagged).

**Recommendation if Not Met**

Adopt Unity Catalog tags for discovery, ownership, and classification.

- Create a tagging taxonomy (owner, domain, pii, retention) and apply tags: <https://docs.databricks.com/aws/en/database-objects/tags>
- Use `INFORMATION_SCHEMA.TABLE_TAGS` to audit coverage: <https://docs.databricks.com/aws/en/sql/language-manual/information-schema/table_tags>
- Consider ABAC later if you want policy-driven tag enforcement at scale.

---

### DG-02-01 — Centralize access control for all data and AI assets

| Field | Value |
|---|---|
| Principle | Unify data and AI security |
| Threshold | 100% |
| waf_cache table | `waf_controls_g` |

**What it measures**

Row-level/column-level controls present (checks existence of Unity Catalog row filters in `system.information_schema.row_filters`). Score is 100 if any row filter exists, 0 otherwise.

**Recommendation if Not Met**

Implement row filters and column masks (or ABAC policies) for sensitive data.

- Start with row filters/column masks per table: <https://docs.databricks.com/aws/en/data-governance/unity-catalog/filters-and-masks/>
- Centralize logic in UDFs / mapping tables and reuse across datasets.
- Validate with least-privilege groups and test with impersonation.

**Detail Query**

??? note "View SQL"
    ```sql
    SELECT
      count(distinct table_catalog, table_schema, table_name) AS count,
      'table_with_filters' AS object_type
    from system.information_schema.row_filters

    UNION ALL

    SELECT
      count(distinct table_catalog, table_schema, table_name),
      'table_with_masks'
    from system.information_schema.column_masks

    UNION ALL

    SELECT
      count(*),
      'column_masks'
    from system.information_schema.column_masks

    UNION ALL

    SELECT
      count(*),
      'row_filters'
    from system.information_schema.row_filters
    ```

---

### DG-02-02 — Configure audit logging

| Field | Value |
|---|---|
| Principle | Unify data and AI security |
| Threshold | 100% |
| waf_cache table | `waf_controls_g` |

**What it measures**

Audit log system table enabled and queryable (checks existence of `system.access.audit`). Score is 100 if the table exists and is queryable, 0 otherwise.

**Recommendation if Not Met**

Enable and grant access to the audit log system table.

- Audit log system table reference: <https://docs.databricks.com/aws/en/admin/system-tables/audit-logs>
- Event catalog/reference for what is logged: <https://docs.databricks.com/aws/en/admin/account-settings/audit-logs>
- Build standard dashboards/alerts (admin actions, permission changes, anomalous access).

**Detail Query**

??? note "View SQL"
    ```sql
    SELECT
      count(*) as count_of_events,
      audit_level,
      workspace_id
    from system.access.audit
    where event_date between current_date() - 30 and current_date()
    group by audit_level, workspace_id
    ```

---

### DG-02-03 — Audit data platform events

| Field | Value |
|---|---|
| Principle | Unify data and AI security |
| Threshold | 100% |
| waf_cache table | `waf_controls_g` |

**What it measures**

Marketplace listing access events available (checks `system.marketplace.listing_access_events` exists). Score is 100 if the table exists, 0 otherwise.

**Recommendation if Not Met**

If you use Databricks Marketplace, enable/confirm marketplace access-event tracking and use it in governance reporting.

- System tables overview and enablement: <https://docs.databricks.com/aws/en/admin/system-tables/>
- Grant read access to the marketplace schema tables for the governance/reporting group.
- Monitor who accessed what listings and when; route to SIEM if required.

**Detail Query**

??? note "View SQL"
    ```sql
    SELECT
      count(*) AS cnt
    FROM system.access.audit
    WHERE service_name = 'unityCatalog'
      AND (
        action_name IN ('deltaSharingQueriedTable','deltaSharingQueriedTableChanges',
                        'generateTemporaryTableCredential','generateTemporaryVolumeCredential')
        OR action_name LIKE 'deltaSharing%'
      )
      AND event_date >= date_add(current_date(), -30)
      AND coalesce(
            request_params['metastore_id'],
            get_json_object(response.result, '$.metastoreId')
          ) = element_at(split(current_metastore(), ':'), 3)
    ORDER BY cnt DESC;
    ```

---

### DG-03-02 — Use data quality tools for profiling, cleansing, validating, and monitoring data

| Field | Value |
|---|---|
| Principle | Establish data quality standards |
| Threshold | 100% |
| waf_cache table | `waf_controls_g` |

**What it measures**

Data quality monitoring artifacts exist (looks for tables with suffix `_drift_metrics` or `_profile_metrics`). Score is 100 if any such table exists, 0 otherwise.

**Recommendation if Not Met**

Adopt platform-native data quality monitoring/profiling and publish the results as drift/profile metrics.

- Standardize profiling for 'gold' datasets (nulls, distribution drift, freshness).
- Use system tables for operational monitoring and build alerting pipelines: <https://docs.databricks.com/aws/en/admin/system-tables/>
- Ensure metric tables are registered in UC and discoverable (tags + comments).

**Detail Query**

??? note "View SQL"
    ```sql
    SELECT COUNT(*) as count_tables
    FROM system.information_schema.tables 
    WHERE table_name LIKE '%_drift_metrics' OR table_name LIKE '%_profile_metrics'
    ```

---

### DG-03-03 — Implement and enforce standardized data formats and definitions

| Field | Value |
|---|---|
| Principle | Establish data quality standards |
| Threshold | 80% |
| waf_cache table | `waf_controls_g` |

**What it measures**

% of UC managed/external tables stored in `DELTA`, `ICEBERG`, or `DELTASHARING` format.

**Recommendation if Not Met**

Standardize on Delta (or Iceberg) for managed reliability and governance.

- Delta Lake overview: <https://docs.databricks.com/aws/en/delta/>
- Why ACID matters on Databricks: <https://docs.databricks.com/aws/en/lakehouse/acid>
- Migrate high-value tables first; keep external formats only for justified interoperability cases.

**Detail Query**

??? note "View SQL"
    ```sql
    SELECT
      COUNT(*) AS count_of_tables,
      table_type,
      data_source_format
    FROM system.information_schema.tables
    GROUP BY table_type, data_source_format
    ```

---
