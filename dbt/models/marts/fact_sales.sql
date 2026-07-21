-- NorthPeak: FactSales mart model
-- Grain: one row per order
-- Phase 5: dbt Transformation Engineering
-- Business owner: CFO (unified revenue reporting)
-- SLA: T+1 by 06:00 UTC

{{
  config(
    materialized='incremental',
    unique_key='order_id',
    schema='marts',
    tags=['gold', 'sales', 'daily', 'finance'],
    on_schema_change='fail',
    post_hook=[
      "analyze {{ this }}"
    ]
  )
}}

with orders as (
    select * from {{ ref('stg_orders') }}
    {% if is_incremental() %}
    where order_day >= (select max(order_day) - interval '3 days' from {{ this }})
    {% endif %}
),

dim_customer as (
    select customer_id, customer_key from {{ ref('dim_customer') }}
),

dim_store as (
    select store_id, store_key from {{ ref('dim_store') }}
),

dim_date as (
    select date_day, date_key from {{ ref('dim_date') }}
),

final as (
    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['o.order_id']) }} as sales_key,

        -- Natural key
        o.order_id,
        o.order_ref,

        -- Foreign keys to dimensions
        coalesce(dc.customer_key, -1)   as customer_key,
        ds.store_key,
        dd.date_key,

        -- Degenerate dimensions
        o.order_channel,
        o.order_status,
        o.payment_method,
        o.customer_id_is_unknown,
        o.is_returned,

        -- Measures
        o.total_amount,
        o.discount_amount,
        o.vat_amount,
        o.net_amount,
        o.loyalty_points_earned,

        -- Audit
        o.order_date,
        o._silver_cleansed_at,
        current_timestamp as _dbt_loaded_at

    from orders o
    left join dim_customer dc on o.customer_id = dc.customer_id
    left join dim_store    ds on o.store_id    = ds.store_id
    left join dim_date     dd on o.order_day   = dd.date_day
)

select * from final
