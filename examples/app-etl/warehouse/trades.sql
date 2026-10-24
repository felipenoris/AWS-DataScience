-- app-etl's governed table (Stage 9 step 9.4): the warehouse copy of the application's table, which
-- the Glue job awsds-prod-app-etl-load writes as awsds-prod-job-exec. The pipeline's manual job
-- production-warehouse-ddl runs this file through the Data API as awsds-deploy-prod, so the table
-- belongs to IAMR:awsds-deploy-prod and the job role writes it through the default privileges 9.3 gave
-- that user's tables in the schema trades. One statement, idempotent: a second run changes nothing.
CREATE TABLE IF NOT EXISTS trades.trades_notional (
    trade_date DATE NOT NULL,
    desk VARCHAR(32) NOT NULL,
    instrument VARCHAR(32) NOT NULL,
    quantity DOUBLE PRECISION NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    notional DOUBLE PRECISION NOT NULL
)
DISTSTYLE AUTO
SORTKEY (trade_date);
