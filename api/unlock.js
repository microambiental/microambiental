const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function safeEqual(a, b) {
  const ab = Buffer.from(a || '', 'utf8');
  const bb = Buffer.from(b || '', 'utf8');
  if (ab.length !== bb.length) return false;
  return crypto.timingSafeEqual(ab, bb);
}

module.exports = (req, res) => {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }
  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body) : (req.body || {});
    const expected = process.env.DASHBOARD_PASSWORD || '';
    if (!expected) return res.status(500).json({ error: 'Server not configured' });
    if (!safeEqual(body.password, expected)) {
      return res.status(401).json({ error: 'unauthorized' });
    }
    const snapshotPath = path.join(process.cwd(), 'data', 'snapshot.json');
    const raw = fs.readFileSync(snapshotPath, 'utf8');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    return res.status(200).send(raw);
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
};
