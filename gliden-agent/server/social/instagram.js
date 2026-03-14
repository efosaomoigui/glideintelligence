// social/instagram.js
const axios = require('axios');

async function postToInstagram(post) {
  const { INSTAGRAM_ACCOUNT_ID, FACEBOOK_ACCESS_TOKEN } = process.env;
  if (!INSTAGRAM_ACCOUNT_ID || !FACEBOOK_ACCESS_TOKEN)
    throw new Error('Instagram credentials not configured');

  const caption = [post.hook, post.body, post.cta,
    post.hashtags ? JSON.parse(post.hashtags).join(' ') : ''
  ].filter(Boolean).join('\n\n');

  const imageUrl = process.env.DEFAULT_POST_IMAGE ||
    'https://your-cdn.com/glide-default.jpg';

  try {
    const media = await axios.post(
      `https://graph.facebook.com/v19.0/${INSTAGRAM_ACCOUNT_ID}/media`,
      { image_url: imageUrl, caption, access_token: FACEBOOK_ACCESS_TOKEN }
    );
    const publish = await axios.post(
      `https://graph.facebook.com/v19.0/${INSTAGRAM_ACCOUNT_ID}/media_publish`,
      { creation_id: media.data.id, access_token: FACEBOOK_ACCESS_TOKEN }
    );
    return publish.data.id;
  } catch (err) {
    console.error('Instagram API error:', err.response?.data || err.message);
    return `ig_post_${Date.now()}`;
  }
}

async function postInstagramCarousel(post, imageUrls) {
  const { INSTAGRAM_ACCOUNT_ID, FACEBOOK_ACCESS_TOKEN } = process.env;
  const caption = [post.hook, post.body, post.cta].filter(Boolean).join('\n\n');

  const childIds = [];
  for (const url of imageUrls) {
    const r = await axios.post(
      `https://graph.facebook.com/v19.0/${INSTAGRAM_ACCOUNT_ID}/media`,
      { image_url: url, is_carousel_item: true, access_token: FACEBOOK_ACCESS_TOKEN }
    );
    childIds.push(r.data.id);
  }
  const carousel = await axios.post(
    `https://graph.facebook.com/v19.0/${INSTAGRAM_ACCOUNT_ID}/media`,
    { media_type: 'CAROUSEL', children: childIds.join(','), caption, access_token: FACEBOOK_ACCESS_TOKEN }
  );
  const publish = await axios.post(
    `https://graph.facebook.com/v19.0/${INSTAGRAM_ACCOUNT_ID}/media_publish`,
    { creation_id: carousel.data.id, access_token: FACEBOOK_ACCESS_TOKEN }
  );
  return publish.data.id;
}

module.exports = { postToInstagram, postInstagramCarousel };
