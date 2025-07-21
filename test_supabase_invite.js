// Test script to send Supabase invitation
// Run this with: node test_supabase_invite.js

const { createClient } = require('@supabase/supabase-js');

// Replace with your Supabase credentials
const supabaseUrl = 'YOUR_SUPABASE_URL';
const supabaseServiceRoleKey = 'YOUR_SERVICE_ROLE_KEY'; // Service role key (not anon key)

const supabase = createClient(supabaseUrl, supabaseServiceRoleKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
});

async function testInviteUser() {
  try {
    const { data, error } = await supabase.auth.admin.inviteUserByEmail(
      'test@example.com', // Replace with test email
      {
        redirectTo: 'http://localhost:3000/accept-invitation',
        data: {
          name: 'Test User',
          role: 'admin'
        }
      }
    );

    if (error) {
      console.error('Error sending invitation:', error);
    } else {
      console.log('Invitation sent successfully:', data);
    }
  } catch (error) {
    console.error('Exception:', error);
  }
}

testInviteUser();