-- Phase 1 data plane — Planner AI v3
-- Target: Postgres 16+ with pgvector
-- Apply: psql -d planner_ai -f db/migrations/001_phase1_data_plane.sql

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Layouts: Raster2Seq geometry authority (Slice A writes here)
CREATE TABLE IF NOT EXISTS layouts (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_version  text NOT NULL DEFAULT '1',
    source_kind     text NOT NULL CHECK (source_kind IN ('image', 'pdf', 'text')),
    content_sha256  text,
    checkpoint_alias text,
    checkpoint_repo  text DEFAULT 'haopt/Raster2Seq',
    scale_meters_per_unit double precision,
    scale_user_confirmed boolean NOT NULL DEFAULT false,
    geometry        jsonb NOT NULL,
    svg             text,
    extrusion       jsonb,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS layouts_content_sha256_idx ON layouts (content_sha256);
CREATE INDEX IF NOT EXISTS layouts_geometry_gin ON layouts USING gin (geometry);

-- Cabinets: catalog products (seeded in later slices; schema only in Phase 1)
CREATE TABLE IF NOT EXISTS cabinets (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sku             text NOT NULL UNIQUE,
    name            text NOT NULL,
    cabinet_type    text NOT NULL CHECK (cabinet_type IN ('base', 'wall', 'tall', 'appliance')),
    width_mm        integer,
    height_mm       integer,
    depth_mm        integer,
    finish_ids      uuid[] DEFAULT '{}',
    metadata        jsonb NOT NULL DEFAULT '{}',
    -- aesthetic / product embedding (dimension chosen at seed time; nullable until catalog slice)
    embedding       vector(512),
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS cabinets_type_idx ON cabinets (cabinet_type);

-- Finishes: user-selectable catalog constraints
CREATE TABLE IF NOT EXISTS finishes (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code            text NOT NULL UNIQUE,
    name            text NOT NULL,
    category        text,
    metadata        jsonb NOT NULL DEFAULT '{}',
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- Sessions: interactive planning state
CREATE TABLE IF NOT EXISTS sessions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    external_ref    text,
    layout_id       uuid REFERENCES layouts (id) ON DELETE SET NULL,
    finish_ids      uuid[] DEFAULT '{}',
    inspiration_uris text[] DEFAULT '{}',
    state           jsonb NOT NULL DEFAULT '{}',
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sessions_layout_id_idx ON sessions (layout_id);

-- Audit log: tool calls, routing, material mutations
CREATE TABLE IF NOT EXISTS audit_log (
    id              bigserial PRIMARY KEY,
    occurred_at     timestamptz NOT NULL DEFAULT now(),
    actor           text NOT NULL DEFAULT 'system',
    action          text NOT NULL,
    session_id      uuid REFERENCES sessions (id) ON DELETE SET NULL,
    layout_id       uuid REFERENCES layouts (id) ON DELETE SET NULL,
    route           text,
    success         boolean,
    duration_ms     integer,
    detail          jsonb NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS audit_log_occurred_at_idx ON audit_log (occurred_at DESC);
CREATE INDEX IF NOT EXISTS audit_log_action_idx ON audit_log (action);
