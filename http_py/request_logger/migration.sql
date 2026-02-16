CREATE TABLE
    IF NOT EXISTS public.request_logger_request (
        -- Meta
        id BIGSERIAL CONSTRAINT request_logger_request_pk PRIMARY KEY,
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

ALTER TABLE public.request_logger_request OWNER TO postgres;

CREATE INDEX IF NOT EXISTS request_logger_request__month_index ON public.request_logger_request (month, product_name, path);

CREATE INDEX IF NOT EXISTS request_logger_request__day_index ON public.request_logger_request (day, product_name, path);

CREATE INDEX IF NOT EXISTS request_logger_request__hour_index ON public.request_logger_request (hour, product_name, path);