resource "aws_glue_catalog_database" "data_lake" {
  count = var.enable_glue_catalog ? 1 : 0

  name        = var.glue_database_name
  description = "AWS Glue Data Catalog database for the data lake event datasets."

  create_table_default_permission {
    permissions = [
      "ALL"
    ]

    principal {
      data_lake_principal_identifier = "IAM_ALLOWED_PRINCIPALS"
    }
  }

  catalog_id = data.aws_caller_identity.current.account_id

  location_uri = "s3://${aws_s3_bucket.raw_data.bucket}/${var.raw_data_prefix}/"

  parameters = {
    project     = local.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "aws_glue_catalog_table" "events" {
  count = var.enable_glue_catalog ? 1 : 0

  name          = var.glue_table_name
  database_name = aws_glue_catalog_database.data_lake[0].name
  catalog_id    = data.aws_caller_identity.current.account_id

  description = "Partitioned event dataset stored in the raw data S3 prefix."

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL                 = "TRUE"
    classification           = "json"
    "projection.enabled"     = "false"
    "compressionType"        = "none"
    "typeOfData"             = "file"
    "has_encrypted_data"     = "true"
    "parquet.compression"    = "SNAPPY"
    "skip.header.line.count" = "0"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.raw_data.bucket}/${var.raw_data_prefix}/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "event-json-serde"
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"

      parameters = {
        "ignore.malformed.json" = "false"
      }
    }

    columns {
      name = "event_id"
      type = "string"
    }

    columns {
      name = "event_timestamp"
      type = "timestamp"
    }

    columns {
      name = "event_date"
      type = "date"
    }

    columns {
      name = "tenant_id"
      type = "string"
    }

    columns {
      name = "event_type"
      type = "string"
    }

    columns {
      name = "user_id"
      type = "string"
    }

    columns {
      name = "amount"
      type = "string"
    }

    columns {
      name = "currency"
      type = "string"
    }

    columns {
      name = "source"
      type = "string"
    }

    columns {
      name = "attributes"
      type = "map<string,string>"
    }
  }

  partition_keys {
    name = "event_date"
    type = "string"
  }

  depends_on = [
    aws_glue_catalog_database.data_lake
  ]
}