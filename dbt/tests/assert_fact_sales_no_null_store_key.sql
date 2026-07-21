-- Singular test: FactSales must never have a null store_key
-- A null store_key means an order came from a store not in DimStore - a data integrity failure.
-- If this test fails, check DimStore is fully populated before running FactSales.

select order_id
from {{ ref('fact_sales') }}
where store_key is null
