-- Add created_at timestamp to audit_events table
ALTER TABLE audit_events 
ADD COLUMN created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();