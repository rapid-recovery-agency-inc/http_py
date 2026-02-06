CREATE EXTENSION postgis;

CREATE EXTENSION postgis_raster;

-- enabling advanced 3d support
CREATE EXTENSION postgis_sfcgal;

-- enabling SQL/MM Net Topology
CREATE EXTENSION postgis_topology;

-- using US census data for geocoding and standardization
CREATE EXTENSION address_standardizer;

CREATE EXTENSION fuzzystrmatch;

CREATE EXTENSION postgis_tiger_geocoder;

CREATE TABLE
    IF NOT EXISTS public.cache (
        id BIGSERIAL NOT NULL CONSTRAINT cache_pkey PRIMARY KEY,
        created_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP NOT NULL,
        updated_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP NOT NULL,
        key BYTEA NOT NULL,
        plain_key TEXT NOT NULL,
        value JSONB NOT NULL
    );

ALTER TABLE public.cache OWNER TO postgres;

-- Hash index for efficient equality lookups on binary key
CREATE INDEX IF NOT EXISTS cache_key_hash_idx ON public.cache USING HASH (key);