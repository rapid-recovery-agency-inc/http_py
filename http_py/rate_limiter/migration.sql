CREATE TABLE
    IF NOT EXISTS public.rate_limiter_rule (
        id BIGSERIAL CONSTRAINT rate_limiter_rule_pk PRIMARY KEY,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        -- Scope
        product_name TEXT NOT NULL,
        path TEXT NOT NULL,
        -- Limits
        hourly_limit INTEGER NOT NULL DEFAULT 0,
        daily_limit INTEGER NOT NULL DEFAULT 0,
        monthly_limit INTEGER NOT NULL DEFAULT 0,
        CONSTRAINT rate_limiter_rule_product_path UNIQUE (product_name, path)
    );

ALTER TABLE public.rate_limiter_rule OWNER TO postgres;

CREATE INDEX rate_limiter_rule_product_name__path_index ON rate_limiter_rule (product_name, path);