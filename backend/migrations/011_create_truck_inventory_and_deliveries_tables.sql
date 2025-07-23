-- Add volume capacity to vehicles table
ALTER TABLE vehicles ADD COLUMN capacity_m3 NUMERIC(10, 2);
ALTER TABLE vehicles ADD COLUMN volume_unit VARCHAR(10) DEFAULT 'm3';

-- Create delivery_status enum
CREATE TYPE delivery_status AS ENUM ('pending', 'delivered', 'failed', 'partial');

-- Create truck_inventory table
CREATE TABLE truck_inventory (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id      UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    vehicle_id   UUID NOT NULL REFERENCES vehicles(id),
    product_id   UUID NOT NULL REFERENCES products(id),
    variant_id   UUID NOT NULL REFERENCES variants(id),
    loaded_qty   NUMERIC(15,3) NOT NULL DEFAULT 0,
    delivered_qty NUMERIC(15,3) NOT NULL DEFAULT 0,
    empties_collected_qty NUMERIC(15,3) NOT NULL DEFAULT 0,
    empties_expected_qty NUMERIC(15,3) NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by   UUID,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by   UUID,
    UNIQUE (trip_id, vehicle_id, product_id, variant_id),
    CONSTRAINT truck_inventory_loaded_qty_non_negative CHECK (loaded_qty >= 0),
    CONSTRAINT truck_inventory_delivered_qty_non_negative CHECK (delivered_qty >= 0),
    CONSTRAINT truck_inventory_empties_collected_qty_non_negative CHECK (empties_collected_qty >= 0),
    CONSTRAINT truck_inventory_empties_expected_qty_non_negative CHECK (empties_expected_qty >= 0),
    CONSTRAINT truck_inventory_delivered_qty_within_loaded CHECK (delivered_qty <= loaded_qty)
);

-- Create delivery_lines table
CREATE TABLE delivery_lines (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delivery_id      UUID NOT NULL REFERENCES deliveries(id) ON DELETE CASCADE,
    order_line_id    UUID NOT NULL REFERENCES order_lines(id),
    product_id       UUID NOT NULL REFERENCES products(id),
    variant_id       UUID NOT NULL REFERENCES variants(id),
    ordered_qty      NUMERIC(15,3) NOT NULL DEFAULT 0,
    delivered_qty    NUMERIC(15,3) NOT NULL DEFAULT 0,
    empties_collected NUMERIC(15,3) NOT NULL DEFAULT 0,
    notes            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT delivery_lines_ordered_qty_non_negative CHECK (ordered_qty >= 0),
    CONSTRAINT delivery_lines_delivered_qty_non_negative CHECK (delivered_qty >= 0),
    CONSTRAINT delivery_lines_empties_collected_non_negative CHECK (empties_collected >= 0)
);

-- Create deliveries table
CREATE TABLE deliveries (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id           UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    order_id          UUID NOT NULL REFERENCES orders(id),
    customer_id       UUID NOT NULL REFERENCES customers(id),
    stop_id           UUID NOT NULL REFERENCES trip_stops(id),
    status            delivery_status NOT NULL DEFAULT 'pending',
    arrival_time      TIMESTAMPTZ,
    completion_time   TIMESTAMPTZ,
    customer_signature TEXT,  -- Base64 encoded signature
    photos            TEXT,   -- JSON array of photo paths/URLs
    notes             TEXT,
    failed_reason     TEXT,
    gps_location      TEXT,   -- JSON: {"longitude": x, "latitude": y}
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by        UUID,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by        UUID,
    UNIQUE (trip_id, order_id)
);

-- Create indexes for better query performance
CREATE INDEX truck_inventory_trip_id_idx ON truck_inventory(trip_id);
CREATE INDEX truck_inventory_vehicle_id_idx ON truck_inventory(vehicle_id);
CREATE INDEX truck_inventory_product_variant_idx ON truck_inventory(product_id, variant_id);

CREATE INDEX delivery_lines_delivery_id_idx ON delivery_lines(delivery_id);
CREATE INDEX delivery_lines_order_line_id_idx ON delivery_lines(order_line_id);
CREATE INDEX delivery_lines_product_variant_idx ON delivery_lines(product_id, variant_id);

CREATE INDEX deliveries_trip_id_idx ON deliveries(trip_id);
CREATE INDEX deliveries_order_id_idx ON deliveries(order_id);
CREATE INDEX deliveries_customer_id_idx ON deliveries(customer_id);
CREATE INDEX deliveries_stop_id_idx ON deliveries(stop_id);
CREATE INDEX deliveries_status_idx ON deliveries(status);
CREATE INDEX deliveries_created_at_idx ON deliveries(created_at);

-- Add comments for documentation
COMMENT ON TABLE truck_inventory IS 'Tracks inventory loaded on vehicles during trips';
COMMENT ON TABLE delivery_lines IS 'Individual product lines delivered to customers';
COMMENT ON TABLE deliveries IS 'Delivery records during trips with proof of delivery';
COMMENT ON COLUMN vehicles.capacity_m3 IS 'Volume capacity in cubic meters';
COMMENT ON COLUMN vehicles.volume_unit IS 'Unit for volume capacity (m3, ft3, etc.)';
COMMENT ON COLUMN truck_inventory.loaded_qty IS 'Quantity loaded on vehicle at start of trip';
COMMENT ON COLUMN truck_inventory.delivered_qty IS 'Quantity delivered to customers during trip';
COMMENT ON COLUMN truck_inventory.empties_collected_qty IS 'Empty cylinders collected from customers';
COMMENT ON COLUMN truck_inventory.empties_expected_qty IS 'Expected empty cylinders to collect';
COMMENT ON COLUMN deliveries.customer_signature IS 'Base64 encoded customer signature for proof of delivery';
COMMENT ON COLUMN deliveries.photos IS 'JSON array of photo paths/URLs for proof of delivery';
COMMENT ON COLUMN deliveries.gps_location IS 'GPS coordinates as JSON: {"longitude": x, "latitude": y}'; 