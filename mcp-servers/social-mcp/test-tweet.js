const { TwitterApi } = require('twitter-api-v2');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config({ path: path.join(__dirname, '../../.env') });

async function postTweet() {
    const appKey = process.env.TWITTER_API_KEY;
    const appSecret = process.env.TWITTER_API_SECRET;
    const accessToken = process.env.TWITTER_ACCESS_TOKEN;
    const accessSecret = process.env.TWITTER_ACCESS_TOKEN_SECRET;

    const client = new TwitterApi({
        appKey,
        appSecret,
        accessToken,
        accessSecret,
    });

    try {
        const content = "Test tweet from AI Employee " + new Date().toISOString();
        const response = await client.v2.tweet(content);
        console.log('Successfully posted to Twitter!');
        console.log('Response:', JSON.stringify(response, null, 2));
    } catch (error) {
        console.error('Twitter post failed:', error);
        process.exit(1);
    }
}

postTweet();
