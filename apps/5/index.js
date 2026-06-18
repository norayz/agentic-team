#!/usr/bin/env node
const app = require('./src/server');

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`🚀 Barista Site running on http://localhost:${PORT}`);
  console.log(`📋 Admin panel: http://localhost:${PORT}/admin`);
});
