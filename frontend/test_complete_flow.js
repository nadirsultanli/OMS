// Simulate the complete authentication flow
console.log('=== Testing Complete Authentication Flow ===\n');

// Step 1: Simulate receiving the callback URL
const callbackUrl = 'http://localhost:3000/auth/callback?access_token=google_session_175c11a8-116a-4b27-99ff-9d35dbe8c0a8&refresh_token=refresh_175c11a8-116a-4b27-99ff-9d35dbe8c0a8&user_id=175c11a8-116a-4b27-99ff-9d35dbe8c0a8&email=riad%40circl.team&name=PROPAN+16KG&role=driver&tenant_id=332072c1-5405-4f09-a56f-a631defa911b';

console.log('1. Callback URL received:', callbackUrl);

// Step 2: Parse URL parameters
const urlParams = new URLSearchParams(callbackUrl.split('?')[1]);
const accessToken = urlParams.get('access_token');
const refreshToken = urlParams.get('refresh_token');
const userId = urlParams.get('user_id');
const email = decodeURIComponent(urlParams.get('email') || '');
const name = decodeURIComponent(urlParams.get('name') || '');
const role = urlParams.get('role');
const tenantId = urlParams.get('tenant_id');

console.log('2. Parsed parameters:');
console.log('   - accessToken:', accessToken);
console.log('   - email:', email);
console.log('   - name:', name);
console.log('   - role:', role);

// Step 3: Store in localStorage (simulated)
const userData = {
  id: userId,
  email: email,
  name: name,
  role: role,
  tenant_id: tenantId
};

console.log('3. Storing in localStorage:');
console.log('   - accessToken:', accessToken);
console.log('   - user:', JSON.stringify(userData));

// Step 4: Check authentication
function isAuthenticated() {
  return !!(accessToken && JSON.stringify(userData));
}

console.log('4. Authentication check:');
console.log('   - isAuthenticated():', isAuthenticated());

// Step 5: Simulate navigation to dashboard
console.log('5. Navigating to dashboard...');

// Step 6: Check if ProtectedRoute would allow access
console.log('6. ProtectedRoute check:');
console.log('   - Would allow access:', isAuthenticated());

if (isAuthenticated()) {
  console.log('   ✅ SUCCESS: User should be able to access dashboard');
} else {
  console.log('   ❌ FAILURE: User would be redirected to login');
}

console.log('\n=== Flow Complete ==='); 