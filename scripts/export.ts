
import fetch from 'node-fetch';

async function main() {
  const res = await fetch('http://localhost:3000/api/exports', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({})
  });
  const json = await res.json();
  console.log(json);
}
main().catch(console.error);
