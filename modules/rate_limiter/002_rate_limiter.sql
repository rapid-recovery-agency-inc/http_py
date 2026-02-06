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

CREATE TABLE
    IF NOT EXISTS public.rate_limiter_request (
        -- Meta
        id BIGSERIAL CONSTRAINT rate_limiter_request_pk PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        -- Scope
        path VARCHAR(255) NOT NULL,
        product_name TEXT NOT NULL,
        product_module TEXT NOT NULL,
        product_feature TEXT NOT NULL,
        product_tenant TEXT NOT NULL,
        month INTEGER DEFAULT (
            (
                EXTRACT(
                    YEAR
                    FROM
                        CURRENT_DATE
                ) * 100
            ) + EXTRACT(
                MONTH
                FROM
                    CURRENT_DATE
            )
        ) NOT NULL,
        day INTEGER DEFAULT (
            (
                EXTRACT(
                    YEAR
                    FROM
                        CURRENT_DATE
                ) * 100
            ) + (
                EXTRACT(
                    MONTH
                    FROM
                        CURRENT_DATE
                ) * 100
            ) + EXTRACT(
                DAY
                FROM
                    CURRENT_DATE
            )
        ) NOT NULL,
        hour INTEGER DEFAULT (
            (
                EXTRACT(
                    YEAR
                    FROM
                        CURRENT_DATE
                ) * 100
            ) + (
                EXTRACT(
                    MONTH
                    FROM
                        CURRENT_DATE
                ) * 100
            ) + (
                EXTRACT(
                    DAY
                    FROM
                        CURRENT_DATE
                ) * 100
            ) + EXTRACT(
                HOUR
                FROM
                    CURRENT_TIMESTAMP
            )
        ) NOT NULL,
        -- Request/Response Data
        from_cache BOOLEAN NOT NULL,
        request_headers TEXT NOT NULL,
        request_body TEXT NOT NULL,
        response_headers TEXT NOT NULL,
        response_body TEXT NOT NULL,
        status_code INTEGER NOT NULL
    );

ALTER TABLE public.rate_limiter_request OWNER TO postgres;

CREATE INDEX IF NOT EXISTS rate_limiter_request__month_index ON public.rate_limiter_request (month, product_name, path);

CREATE INDEX IF NOT EXISTS rate_limiter_request__day_index ON public.rate_limiter_request (day, product_name, path);

CREATE INDEX IF NOT EXISTS rate_limiter_request__hour_index ON public.rate_limiter_request (hour, product_name, path);