// Test the authentication logic
console.log('Testing isAuthenticated logic:');

const token = 'google_session_175c11a8-116a-4b27-99ff-9d35dbe8c0a8';
const user = '{"id":"175c11a8-116a-4b27-99ff-9d35dbe8c0a8","email":"riad@circl.team","name":"PROPAN 16KG","role":"driver","tenant_id":"332072c1-5405-4f09-a56f-a631defa911b"}';

console.log('Token exists:', !!token);
console.log('User exists:', !!user);
console.log('isAuthenticated:', !!(token && user));

// Test URL parameter parsing
const urlParams = new URLSearchParams('access_token=google_session_175c11a8-116a-4b27-99ff-9d35dbe8c0a8&refresh_token=refresh_175c11a8-116a-4b27-99ff-9d35dbe8c0a8&user_id=175c11a8-116a-4b27-99ff-9d35dbe8c0a8&email=riad%40circl.team&name=PROPAN+16KG&role=driver&tenant_id=332072c1-5405-4f09-a56f-a631defa911b');

console.log('\nURL parameter parsing:');
console.log('accessToken:', urlParams.get('access_token'));
console.log('email:', decodeURIComponent(urlParams.get('email') || ''));
console.log('name:', decodeURIComponent(urlParams.get('name') || '')); 