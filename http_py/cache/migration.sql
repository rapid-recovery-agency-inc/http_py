-- Cache table for DatabaseCache implementation
-- Stores key-value pairs with optional TTL expiration

CREATE TABLE IF NOT EXISTS public.cache (
    id BIGSERIAL NOT NULL CONSTRAINT cache_pkey PRIMARY KEY,
    created_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP NOT NULL,
    key BYTEA NOT NULL UNIQUE,
    plain_key TEXT NOT NULL,
    value JSONB NOT NULL,
    expires_at BIGINT  -- Unix timestamp in seconds, NULL means never expires
);

ALTER TABLE public.cache OWNER TO postgres;

-- Hash index for efficient equality lookups on binary key
CREATE INDEX IF NOT EXISTS cache_key_hash_idx ON public.cache USING HASH (key);

-- Index for cleanup of expired items
CREATE INDEX IF NOT EXISTS cache_expires_at_idx ON public.cache (expires_at)
    WHERE expires_at IS NOT NULL;

-- Function to cleanup expired cache items (call periodically via cron/scheduler)
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.cache
    WHERE expires_at IS NOT NULL
      AND expires_at <= EXTRACT(EPOCH FROM NOW())::BIGINT;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
