console.log('Testing server storage...'); 
const storageKey = 'homelab_servers';
const stored = localStorage.getItem(storageKey);
console.log('Storage key:', storageKey);
console.log('Data exists:', !!stored);
if (stored) {
  const data = JSON.parse(stored);
  console.log('Server count:', data.servers ? data.servers.length : 0);
  console.log('Data version:', data.version);
  console.log('Updated at:', data.updated_at);
  console.log('First server:', data.servers && data.servers[0] ? data.servers[0].name : 'None');
}

