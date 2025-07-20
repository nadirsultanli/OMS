-- Add auth_user_id column to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS auth_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE;

-- Create index for auth_user_id
CREATE INDEX IF NOT EXISTS idx_users_auth_user_id ON users(auth_user_id);