-- init_db.sql — Run once at container first start
-- Enables the pgvector extension in the jeevanpath database.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- for BM25-style trigram search
