SELECT *
FROM `${source_project_id}.${source_dataset}.${source_table}`
WHERE ${filter_conditions}
  AND created_at >= ${start_date_sql}%{if additional_where != ""}
  AND ${additional_where}%{endif}