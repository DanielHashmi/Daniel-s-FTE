const { TwitterApi } = require('twitter-api-v2');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config({ path: path.join(__dirname, '../../.env') });

async function testTwitter() {
    const appKey = process.env.TWITTER_API_KEY;
    const appSecret = process.env.TWITTER_API_SECRET;
    const accessToken = process.env.TWITTER_ACCESS_TOKEN;
    const accessSecret = process.env.TWITTER_ACCESS_TOKEN_SECRET;

    if (!appKey || !appSecret || !accessToken || !accessSecret) {
        console.error('Twitter credentials missing');
        process.exit(1);
    }

    const client = new TwitterApi({
        appKey,
        appSecret,
        accessToken,
        accessSecret,
    });

    try {
        const user = await client.v2.me({
            "user.fields": ["description", "public_metrics", "verified", "verified_type"]
        });
        console.log('Successfully connected to Twitter!');
        console.log('User Details:', JSON.stringify(user.data, null, 2));
    } catch (error) {
        console.error('Twitter verification failed:', error);
        process.exit(1);
    }
}

testTwitter();
