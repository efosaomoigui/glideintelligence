/**
 * GLIDE Agent Server
 * GlidenIntelligence Social Media Marketing Agent
 * 
 * This server handles:
 * - WhatsApp webhook (receive & send messages)
 * - REST API for admin dashboard
 * - Social media posting queue
 * - Analytics collection
 * - Agent orchestration via Claude API
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const cron = require('node-cron');
const Database = require('better-sqlite3');
const Anthropic = require('@anthropic-ai/sdk');
const twilio = require('twilio');
const fs = require('fs');
const path = require('path');

// ── Social Media Modules ──────────────────────────────────────────────────────
const { postToTikTok } = require('./social/tiktok');
const { postToFacebook } = require('./social/facebook');
const { postToInstagram } = require('./social/instagram');
const { postToTwitter } = require('./social/twitter');
const { collectAllAnalytics } = require('./analytics/collector');

// ── Init ──────────────────────────────────────────────────────────────────────
const app = express();
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ── Database Setup ────────────────────────────────────────────────────────────
const dbDir = path.join(__dirname, '../data');
if (!fs.existsSync(dbDir)) fs.mkdirSync(dbDir, { recursive: true });

const db = new Database(path.join(dbDir, 'gliden.db'));

db.exec(`
  CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    hook TEXT NOT NULL,
    body TEXT NOT NULL,
    cta TEXT NOT NULL,
    image_prompts TEXT,
    caption TEXT,
    hashtags TEXT,
    status TEXT DEFAULT 'draft',
    platform_post_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    posted_at DATETIME,
    scheduled_for DATETIME
  );

  CREATE TABLE IF NOT EXISTS analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    platform TEXT NOT NULL,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id)
  );

  CREATE TABLE IF NOT EXISTS hooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    platform TEXT,
    avg_views REAL DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    last_used DATETIME,
    status TEXT DEFAULT 'untested'
  );

  CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
  );

  INSERT OR IGNORE INTO settings (key, value) VALUES
    ('auto_post_tiktok', 'false'),
    ('auto_post_facebook', 'true'),
    ('auto_post_instagram', 'true'),
    ('auto_post_twitter', 'true'),
    ('posting_paused', 'false'),
    ('daily_post_limit', '4'),
    ('agent_name', 'GLIDE');
`);

// ── Anthropic Claude Client ───────────────────────────────────────────────────
const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// ── Twilio WhatsApp Client ────────────────────────────────────────────────────
const twilioClient = twilio(
  process.env.TWILIO_ACCOUNT_SID,
  process.env.TWILIO_AUTH_TOKEN
);

// ── Load Skill File ───────────────────────────────────────────────────────────
const skillPath = path.join(__dirname, '../GLIDEN_SKILL.md');
const GLIDE_SKILL = fs.existsSync(skillPath)
  ? fs.readFileSync(skillPath, 'utf8')
  : 'You are GLIDE, the GlidenIntelligence marketing agent.';

// ── Load Memory Files ─────────────────────────────────────────────────────────
function loadMemory() {
  const memDir = path.join(__dirname, '../memory');
  if (!fs.existsSync(memDir)) fs.mkdirSync(memDir, { recursive: true });

  const files = ['performance-history.md', 'hook-library.md', 'audience-insights.md', 'brand-voice.md'];
  let memory = '';
  for (const file of files) {
    const fp = path.join(memDir, file);
    if (fs.existsSync(fp)) {
      memory += `\n\n--- ${file} ---\n${fs.readFileSync(fp, 'utf8')}`;
    }
  }
  return memory;
}

// ── Agent Core: Chat with GLIDE ───────────────────────────────────────────────
async function chatWithGlide(userMessage, includeContext = true) {
  // Save user message
  db.prepare('INSERT INTO conversations (role, content) VALUES (?, ?)').run('user', userMessage);

  // Get recent conversation history (last 20 messages)
  const history = db.prepare(
    'SELECT role, content FROM conversations ORDER BY created_at DESC LIMIT 20'
  ).all().reverse();

  // Build messages for Claude
  const messages = history.map(h => ({ role: h.role, content: h.content }));

  // Build system prompt with skill + context
  let systemPrompt = GLIDE_SKILL;

  if (includeContext) {
    const memory = loadMemory();
    if (memory) systemPrompt += `\n\n## YOUR MEMORY\n${memory}`;

    // Add recent analytics context
    const recentAnalytics = db.prepare(`
      SELECT p.platform, p.hook, a.views, a.likes, a.clicks
      FROM posts p LEFT JOIN analytics a ON p.id = a.post_id
      WHERE p.status = 'posted'
      ORDER BY a.recorded_at DESC LIMIT 10
    `).all();
    if (recentAnalytics.length > 0) {
      systemPrompt += `\n\n## RECENT POST PERFORMANCE\n${JSON.stringify(recentAnalytics, null, 2)}`;
    }
  }

  const response = await anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 2048,
    system: systemPrompt,
    messages: messages
  });

  const assistantMessage = response.content[0].text;

  // Save assistant response
  db.prepare('INSERT INTO conversations (role, content) VALUES (?, ?)').run('assistant', assistantMessage);

  // Parse if response contains structured content (JSON blocks)
  const jsonMatch = assistantMessage.match(/```json\n([\s\S]*?)\n```/);
  if (jsonMatch) {
    try {
      const parsed = JSON.parse(jsonMatch[1]);
      await handleStructuredAgentResponse(parsed);
    } catch (e) {
      console.log('Could not parse JSON from agent response:', e.message);
    }
  }

  return assistantMessage;
}

// ── Handle Structured Agent Responses ────────────────────────────────────────
async function handleStructuredAgentResponse(data) {
  if (data.action === 'create_posts' && data.posts) {
    for (const post of data.posts) {
      db.prepare(`
        INSERT INTO posts (platform, hook, body, cta, image_prompts, caption, hashtags, status, scheduled_for)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?)
      `).run(
        post.platform,
        post.hook,
        post.body,
        post.cta,
        JSON.stringify(post.image_prompts || []),
        post.caption || '',
        JSON.stringify(post.hashtags || []),
        post.scheduled_for || null
      );
    }
    console.log(`✅ Saved ${data.posts.length} posts to draft queue`);
  }

  if (data.action === 'save_hook' && data.hook) {
    db.prepare(`
      INSERT OR IGNORE INTO hooks (text, platform, status) VALUES (?, ?, 'untested')
    `).run(data.hook.text, data.hook.platform || 'all');
  }
}

// ── WhatsApp: Send Message ────────────────────────────────────────────────────
async function sendWhatsApp(message) {
  try {
    await twilioClient.messages.create({
      from: `whatsapp:${process.env.TWILIO_WHATSAPP_NUMBER}`,
      to: `whatsapp:${process.env.OWNER_WHATSAPP_NUMBER}`,
      body: message
    });
    console.log('✅ WhatsApp message sent');
  } catch (err) {
    console.error('❌ WhatsApp send error:', err.message);
  }
}

// ── WhatsApp Webhook ──────────────────────────────────────────────────────────
app.post('/webhook/whatsapp', async (req, res) => {
  res.sendStatus(200); // Acknowledge immediately

  const incomingMsg = req.body.Body?.trim();
  const from = req.body.From;

  if (!incomingMsg) return;

  // Only respond to owner's number
  const ownerNumber = `whatsapp:${process.env.OWNER_WHATSAPP_NUMBER}`;
  if (from !== ownerNumber) {
    console.log('Message from unknown number, ignoring:', from);
    return;
  }

  console.log(`📱 WhatsApp from owner: "${incomingMsg}"`);

  // Handle special commands
  const cmd = incomingMsg.toLowerCase();

  if (cmd === 'pause') {
    db.prepare("UPDATE settings SET value = 'true' WHERE key = 'posting_paused'").run();
    await sendWhatsApp('⏸️ *GLIDE:* All posting has been paused. Send "resume" to continue.');
    return;
  }

  if (cmd === 'resume') {
    db.prepare("UPDATE settings SET value = 'false' WHERE key = 'posting_paused'").run();
    await sendWhatsApp('▶️ *GLIDE:* Posting resumed! I\'m back on it.');
    return;
  }

  if (cmd === 'status') {
    const stats = getDashboardStats();
    await sendWhatsApp(
      `📊 *GLIDE Status Report*\n\n` +
      `Posts this week: ${stats.postsThisWeek}\n` +
      `Total views (7d): ${stats.totalViews.toLocaleString()}\n` +
      `Drafts queued: ${stats.draftsQueued}\n` +
      `Posting: ${stats.postingPaused ? '⏸ PAUSED' : '▶️ ACTIVE'}\n\n` +
      `Platforms: TikTok ${stats.platforms.tiktok} | FB ${stats.platforms.facebook} | IG ${stats.platforms.instagram} | X ${stats.platforms.twitter}`
    );
    return;
  }

  // For all other messages, route to GLIDE agent
  try {
    await sendWhatsApp('🤔 *GLIDE:* On it...');
    const response = await chatWithGlide(incomingMsg);
    
    // Split long responses into chunks (WhatsApp has 1600 char limit)
    const chunks = response.match(/.{1,1500}(\s|$)/gs) || [response];
    for (const chunk of chunks) {
      await sendWhatsApp(`*GLIDE:* ${chunk.trim()}`);
    }
  } catch (err) {
    console.error('Agent error:', err);
    await sendWhatsApp('❌ *GLIDE:* I hit an error. Check the dashboard for details.');
  }
});

// ── Dashboard Stats Helper ────────────────────────────────────────────────────
function getDashboardStats() {
  const postsThisWeek = db.prepare(`
    SELECT COUNT(*) as count FROM posts 
    WHERE created_at >= datetime('now', '-7 days')
  `).get().count;

  const totalViews = db.prepare(`
    SELECT COALESCE(SUM(views), 0) as total FROM analytics 
    WHERE recorded_at >= datetime('now', '-7 days')
  `).get().total;

  const draftsQueued = db.prepare(`
    SELECT COUNT(*) as count FROM posts WHERE status = 'draft'
  `).get().count;

  const postingPaused = db.prepare(
    "SELECT value FROM settings WHERE key = 'posting_paused'"
  ).get()?.value === 'true';

  const platforms = {
    tiktok: db.prepare("SELECT COUNT(*) as c FROM posts WHERE platform='tiktok' AND status='posted'").get().c,
    facebook: db.prepare("SELECT COUNT(*) as c FROM posts WHERE platform='facebook' AND status='posted'").get().c,
    instagram: db.prepare("SELECT COUNT(*) as c FROM posts WHERE platform='instagram' AND status='posted'").get().c,
    twitter: db.prepare("SELECT COUNT(*) as c FROM posts WHERE platform='twitter' AND status='posted'").get().c,
  };

  return { postsThisWeek, totalViews, draftsQueued, postingPaused, platforms };
}

// ─────────────────────────────────────────────────────────────────────────────
// REST API ENDPOINTS (for Admin Dashboard)
// ─────────────────────────────────────────────────────────────────────────────

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', agent: 'GLIDE', version: '1.0.0', timestamp: new Date() });
});

// Dashboard stats
app.get('/api/stats', (req, res) => {
  res.json(getDashboardStats());
});

// Get all posts
app.get('/api/posts', (req, res) => {
  const { platform, status, limit = 50 } = req.query;
  let query = 'SELECT * FROM posts';
  const params = [];
  const where = [];

  if (platform) { where.push('platform = ?'); params.push(platform); }
  if (status) { where.push('status = ?'); params.push(status); }
  if (where.length) query += ' WHERE ' + where.join(' AND ');

  query += ' ORDER BY created_at DESC LIMIT ?';
  params.push(parseInt(limit));

  res.json(db.prepare(query).all(...params));
});

// Get single post
app.get('/api/posts/:id', (req, res) => {
  const post = db.prepare('SELECT * FROM posts WHERE id = ?').get(req.params.id);
  if (!post) return res.status(404).json({ error: 'Post not found' });
  const analytics = db.prepare('SELECT * FROM analytics WHERE post_id = ?').all(req.params.id);
  res.json({ ...post, analytics });
});

// Approve and queue a draft post
app.post('/api/posts/:id/approve', async (req, res) => {
  const post = db.prepare('SELECT * FROM posts WHERE id = ?').get(req.params.id);
  if (!post) return res.status(404).json({ error: 'Post not found' });

  db.prepare("UPDATE posts SET status = 'approved' WHERE id = ?").run(req.params.id);
  res.json({ success: true, message: 'Post approved and queued for posting' });

  // Auto-post if enabled for this platform
  const autoPostKey = `auto_post_${post.platform}`;
  const autoPost = db.prepare('SELECT value FROM settings WHERE key = ?').get(autoPostKey)?.value === 'true';
  const paused = db.prepare("SELECT value FROM settings WHERE key = 'posting_paused'").get()?.value === 'true';

  if (autoPost && !paused) {
    await postContent(post);
  }
});

// Manual post now
app.post('/api/posts/:id/post-now', async (req, res) => {
  const post = db.prepare('SELECT * FROM posts WHERE id = ?').get(req.params.id);
  if (!post) return res.status(404).json({ error: 'Post not found' });

  try {
    await postContent(post);
    res.json({ success: true, message: `Posted to ${post.platform}` });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Delete a post
app.delete('/api/posts/:id', (req, res) => {
  db.prepare('DELETE FROM posts WHERE id = ?').run(req.params.id);
  res.json({ success: true });
});

// Get analytics
app.get('/api/analytics', (req, res) => {
  const { days = 7 } = req.query;
  const data = db.prepare(`
    SELECT p.platform, p.hook, a.views, a.likes, a.comments, a.shares, a.clicks, a.recorded_at
    FROM posts p LEFT JOIN analytics a ON p.id = a.post_id
    WHERE a.recorded_at >= datetime('now', '-${parseInt(days)} days')
    ORDER BY a.views DESC
  `).all();
  res.json(data);
});

// Analytics overview per platform
app.get('/api/analytics/overview', (req, res) => {
  const platforms = ['tiktok', 'facebook', 'instagram', 'twitter'];
  const overview = {};

  for (const platform of platforms) {
    overview[platform] = db.prepare(`
      SELECT 
        COUNT(DISTINCT p.id) as total_posts,
        COALESCE(SUM(a.views), 0) as total_views,
        COALESCE(SUM(a.likes), 0) as total_likes,
        COALESCE(SUM(a.comments), 0) as total_comments,
        COALESCE(SUM(a.clicks), 0) as total_clicks,
        COALESCE(AVG(a.views), 0) as avg_views
      FROM posts p LEFT JOIN analytics a ON p.id = a.post_id
      WHERE p.platform = ? AND p.status = 'posted'
    `).get(platform);
  }

  res.json(overview);
});

// Get hooks library
app.get('/api/hooks', (req, res) => {
  const hooks = db.prepare(
    'SELECT * FROM hooks ORDER BY avg_views DESC'
  ).all();
  res.json(hooks);
});

// Get settings
app.get('/api/settings', (req, res) => {
  const settings = db.prepare('SELECT * FROM settings').all();
  const obj = {};
  settings.forEach(s => { obj[s.key] = s.value; });
  res.json(obj);
});

// Update settings
app.put('/api/settings', (req, res) => {
  const updates = req.body;
  const stmt = db.prepare('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)');
  for (const [key, value] of Object.entries(updates)) {
    stmt.run(key, String(value));
  }
  res.json({ success: true });
});

// Chat with GLIDE from dashboard
app.post('/api/chat', async (req, res) => {
  const { message } = req.body;
  if (!message) return res.status(400).json({ error: 'Message required' });

  try {
    const response = await chatWithGlide(message);
    res.json({ response });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get conversation history
app.get('/api/conversations', (req, res) => {
  const history = db.prepare(
    'SELECT * FROM conversations ORDER BY created_at DESC LIMIT 100'
  ).all().reverse();
  res.json(history);
});

// Generate content via GLIDE
app.post('/api/generate', async (req, res) => {
  const { platforms, count = 7, theme } = req.body;

  const prompt = `Generate ${count} social media posts for GlidenIntelligence.
Platforms: ${(platforms || ['tiktok', 'facebook', 'instagram', 'twitter']).join(', ')}
${theme ? `Theme/focus: ${theme}` : ''}

For each post, return a JSON block with this structure:
\`\`\`json
{
  "action": "create_posts",
  "posts": [
    {
      "platform": "tiktok",
      "hook": "The hook text for slide 1",
      "body": "Body content / slide text",
      "cta": "Try GlidenIntelligence free → link",
      "image_prompts": ["Description for image 1", "Description for image 2"],
      "caption": "Full caption with hashtags for the post",
      "hashtags": ["#AI", "#BusinessIntelligence"],
      "scheduled_for": null
    }
  ]
}
\`\`\`

Make them high quality, platform-native, and conversion-focused.`;

  try {
    const response = await chatWithGlide(prompt);
    res.json({ response, message: 'Content generation complete. Check drafts.' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── Post Content to Platforms ─────────────────────────────────────────────────
async function postContent(post) {
  let platformPostId = null;

  try {
    switch (post.platform) {
      case 'tiktok':
        platformPostId = await postToTikTok(post);
        break;
      case 'facebook':
        platformPostId = await postToFacebook(post);
        break;
      case 'instagram':
        platformPostId = await postToInstagram(post);
        break;
      case 'twitter':
        platformPostId = await postToTwitter(post);
        break;
    }

    db.prepare(`
      UPDATE posts SET status = 'posted', platform_post_id = ?, posted_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `).run(platformPostId, post.id);

    // Notify owner via WhatsApp
    await sendWhatsApp(
      `✅ *GLIDE:* Posted to ${post.platform}!\n\n` +
      `Hook: "${post.hook.substring(0, 80)}..."\n\n` +
      `I'll check analytics in 24 hours.`
    );

    // Schedule analytics check in 24h
    setTimeout(async () => {
      await collectAndStoreAnalytics(post.id, post.platform, platformPostId);
    }, 24 * 60 * 60 * 1000);

  } catch (err) {
    console.error(`❌ Failed to post to ${post.platform}:`, err.message);
    db.prepare("UPDATE posts SET status = 'failed' WHERE id = ?").run(post.id);
    await sendWhatsApp(`❌ *GLIDE:* Failed to post to ${post.platform}: ${err.message}`);
  }
}

// ── Collect Analytics ─────────────────────────────────────────────────────────
async function collectAndStoreAnalytics(postId, platform, platformPostId) {
  try {
    const metrics = await collectAllAnalytics(platform, platformPostId);

    db.prepare(`
      INSERT INTO analytics (post_id, platform, views, likes, comments, shares, clicks)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `).run(postId, platform, metrics.views, metrics.likes, metrics.comments, metrics.shares, metrics.clicks);

    // Update hook performance
    const post = db.prepare('SELECT hook FROM posts WHERE id = ?').get(postId);
    if (post) {
      const existing = db.prepare('SELECT * FROM hooks WHERE text = ?').get(post.hook);
      if (existing) {
        const newAvg = (existing.avg_views * existing.usage_count + metrics.views) / (existing.usage_count + 1);
        db.prepare('UPDATE hooks SET avg_views = ?, usage_count = usage_count + 1 WHERE text = ?')
          .run(newAvg, post.hook);
      }
    }

    console.log(`📊 Analytics recorded for post ${postId}: ${JSON.stringify(metrics)}`);
  } catch (err) {
    console.error('Analytics collection error:', err.message);
  }
}

// ── Scheduled Jobs ────────────────────────────────────────────────────────────

// Every day at 8am - generate and queue content for the day
cron.schedule('0 8 * * *', async () => {
  const paused = db.prepare("SELECT value FROM settings WHERE key = 'posting_paused'").get()?.value === 'true';
  if (paused) return;

  console.log('🕗 Running daily content generation...');
  await chatWithGlide(
    'It\'s the morning briefing time. Check the analytics from yesterday, then generate and queue today\'s content for all platforms. Focus on what\'s been working best. Send me a brief WhatsApp summary.'
  );
});

// Every Monday at 9am - weekly report
cron.schedule('0 9 * * 1', async () => {
  console.log('📋 Running weekly report...');
  const response = await chatWithGlide(
    'Please generate this week\'s full performance report. Include total views, best posts, what worked and what didn\'t, and your recommended strategy for the coming week.'
  );
  await sendWhatsApp(`📋 *Weekly Report*\n\n${response}`);
});

// Every 6 hours - collect analytics for recent posts
cron.schedule('0 */6 * * *', async () => {
  console.log('📊 Collecting analytics...');
  const recentPosts = db.prepare(`
    SELECT id, platform, platform_post_id FROM posts 
    WHERE status = 'posted' 
    AND posted_at >= datetime('now', '-7 days')
    AND platform_post_id IS NOT NULL
  `).all();

  for (const post of recentPosts) {
    await collectAndStoreAnalytics(post.id, post.platform, post.platform_post_id);
  }
});

// ── Start Server ──────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`
  ╔═══════════════════════════════════════╗
  ║   GLIDE Agent Server — GlidenIntelligence   ║
  ╠═══════════════════════════════════════╣
  ║  Server:    http://localhost:${PORT}       ║
  ║  Dashboard: http://localhost:3000     ║
  ║  WhatsApp:  /webhook/whatsapp         ║
  ╚═══════════════════════════════════════╝
  `);

  // Morning WhatsApp greeting
  sendWhatsApp('🌅 *GLIDE is online!* Good morning. Ready to market GlidenIntelligence. Send "status" for a report or just talk to me normally.').catch(() => {});
});

module.exports = { app, db, chatWithGlide, sendWhatsApp };
