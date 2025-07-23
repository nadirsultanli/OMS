-- Create trip_status enum
CREATE TYPE trip_status AS ENUM ('draft', 'planned', 'in_progress', 'completed', 'cancelled');

-- Create trips table
CREATE TABLE trips (
    id           UUID PRIMARY KEY,
    tenant_id    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    trip_no      TEXT NOT NULL,
    trip_status  trip_status NOT NULL DEFAULT 'draft',
    vehicle_id   UUID REFERENCES vehicles(id),
    driver_id    UUID REFERENCES users(id),
    planned_date DATE,
    start_time   TIMESTAMPTZ,
    end_time     TIMESTAMPTZ,
    start_wh_id  UUID REFERENCES warehouses(id),
    end_wh_id    UUID REFERENCES warehouses(id),
    gross_loaded_kg NUMERIC(12,3) DEFAULT 0,
    notes        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by   UUID,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by   UUID,
    deleted_at   TIMESTAMPTZ,
    deleted_by   UUID,
    UNIQUE (tenant_id, trip_no)
);

-- Create indexes for trips table
CREATE INDEX trips_tenant_status_idx ON trips(tenant_id, trip_status) WHERE deleted_at IS NULL;
CREATE INDEX trips_vehicle_date_idx ON trips(vehicle_id, planned_date) WHERE deleted_at IS NULL;
CREATE INDEX trips_driver_date_idx ON trips(driver_id, planned_date) WHERE deleted_at IS NULL;
CREATE INDEX trips_created_at_idx ON trips(created_at) WHERE deleted_at IS NULL;

-- Create trip_stops table
CREATE TABLE trip_stops (
    id           UUID PRIMARY KEY,
    trip_id      UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    stop_no      INTEGER NOT NULL,
    order_id     UUID REFERENCES orders(id),
    location     GEOGRAPHY(POINT,4326),
    arrival_time TIMESTAMPTZ,
    departure_time TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by   UUID,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by   UUID,
    UNIQUE (trip_id, stop_no)
);

-- Create indexes for trip_stops table
CREATE INDEX trip_stops_trip_id_idx ON trip_stops(trip_id);
CREATE INDEX trip_stops_order_id_idx ON trip_stops(order_id) WHERE order_id IS NOT NULL;
CREATE INDEX trip_stops_location_idx ON trip_stops USING GIST(location) WHERE location IS NOT NULL;

-- Add comments for documentation
COMMENT ON TABLE trips IS 'Stores trip information for vehicle routing and delivery management';
COMMENT ON TABLE trip_stops IS 'Stores individual stops within a trip, including customer deliveries and collections';
COMMENT ON COLUMN trips.trip_no IS 'Unique trip number within a tenant';
COMMENT ON COLUMN trips.trip_status IS 'Current status of the trip';
COMMENT ON COLUMN trips.gross_loaded_kg IS 'Total weight loaded on the vehicle for this trip';
COMMENT ON COLUMN trip_stops.stop_no IS 'Sequential stop number within the trip';
COMMENT ON COLUMN trip_stops.location IS 'Geographic location of the stop (longitude, latitude)'; 