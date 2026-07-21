-- NorthPeak: Staging model for orders
-- Source: Silver layer Delta table
-- Phase 5: dbt Transformation Engineering

{{
  config(
    materialized='view',
    schema='staging',
    tags=['staging', 'orders', 'daily']
  )
}}

with source as (
    select * from {{ source('silver', 'orders') }}
),

renamed as (
    select
        -- Keys
        order_id,
        order_ref,
        customer_id,
        store_id,

        -- Flags
        customer_id_is_unknown,
        is_returned,

        -- Dimensions
        order_channel,
        order_status,
        payment_method,

        -- Dates
        cast(order_date as timestamp)    as order_date,
        cast(completed_at as timestamp)  as completed_at,
        date_trunc('day', order_date)    as order_day,
        date_trunc('month', order_date)  as order_month,

        -- Amounts (already validated positive in Silver)
        total_amount,
        discount_amount,
        vat_amount,
        total_amount - discount_amount   as net_amount,

        -- Loyalty
        loyalty_points_earned,

        -- Metadata
        _silver_cleansed_at,
        _silver_version

    from source
    where order_status != 'cancelled'   -- exclude cancelled orders from marts
)

select * from renamed
