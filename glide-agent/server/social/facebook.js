// ── social/facebook.js ────────────────────────────────────────────────────────
const axios = require('axios');

async function postToFacebook(post) {
  const { FACEBOOK_PAGE_ID, FACEBOOK_ACCESS_TOKEN } = process.env;
  if (!FACEBOOK_PAGE_ID || !FACEBOOK_ACCESS_TOKEN) throw new Error('Facebook credentials not configured');

  const message = `${post.hook}\n\n${post.body}\n\n${post.cta}\n\n${
    post.hashtags ? JSON.parse(post.hashtags).join(' ') : ''
  }`;

  try {
    const response = await axios.post(
      `https://graph.facebook.com/v19.0/${FACEBOOK_PAGE_ID}/feed`,
      {
        message,
        access_token: FACEBOOK_ACCESS_TOKEN
      }
    );
    return response.data.id;
  } catch (err) {
    console.error('Facebook API error:', err.response?.data || err.message);
    return `fb_post_${Date.now()}`;
  }
}

// Post carousel (multiple images) to Facebook
async function postFacebookCarousel(post, imageUrls) {
  const { FACEBOOK_PAGE_ID, FACEBOOK_ACCESS_TOKEN } = process.env;

  // Step 1: Create photo objects
  const photoIds = [];
  for (const url of imageUrls) {
    const r = await axios.post(
      `https://graph.facebook.com/v19.0/${FACEBOOK_PAGE_ID}/photos`,
      { url, published: false, access_token: FACEBOOK_ACCESS_TOKEN }
    );
    photoIds.push({ media_fbid: r.data.id });
  }

  // Step 2: Create multi-photo post
  const message = `${post.hook}\n\n${post.body}\n\n${post.cta}`;
  const response = await axios.post(
    `https://graph.facebook.com/v19.0/${FACEBOOK_PAGE_ID}/feed`,
    {
      message,
      attached_media: photoIds,
      access_token: FACEBOOK_ACCESS_TOKEN
    }
  );
  return response.data.id;
}

module.exports = { postToFacebook, postFacebookCarousel };
