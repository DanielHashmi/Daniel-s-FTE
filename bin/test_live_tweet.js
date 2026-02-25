#!/usr/bin/env node
/**
 * Direct Twitter Post Test
 * Posts directly to Twitter without approval workflow
 * Run: node test_live_tweet.js "Your tweet message"
 */

require('dotenv').config();
const { TwitterApi } = require('twitter-api-v2');

async function postTweet(message) {
    console.log('\n🐦 Twitter Live Post Test\n');

    // Check credentials
    const appKey = process.env.TWITTER_API_KEY;
    const appSecret = process.env.TWITTER_API_SECRET;
    const accessToken = process.env.TWITTER_ACCESS_TOKEN;
    const accessSecret = process.env.TWITTER_ACCESS_TOKEN_SECRET;

    if (!appKey || !appSecret || !accessToken || !accessSecret) {
        console.error('❌ Twitter credentials not configured in .env');
        console.log('\nRequired variables:');
        console.log('  TWITTER_API_KEY');
        console.log('  TWITTER_API_SECRET');
        console.log('  TWITTER_ACCESS_TOKEN');
        console.log('  TWITTER_ACCESS_TOKEN_SECRET');
        process.exit(1);
    }

    console.log('✓ Twitter credentials found');
    console.log(`📝 Message: "${message}"`);
    console.log(`📏 Length: ${message.length}/280 characters\n`);

    if (message.length > 280) {
        console.error('❌ Tweet too long! Maximum 280 characters.');
        process.exit(1);
    }

    // Confirm before posting
    console.log('⚠️  This will post a REAL tweet to your account!');
    console.log('    Press Ctrl+C within 3 seconds to cancel...\n');

    await new Promise(resolve => setTimeout(resolve, 3000));

    try {
        // Initialize client
        const client = new TwitterApi({
            appKey,
            appSecret,
            accessToken,
            accessSecret,
        });

        console.log('📤 Posting to Twitter...');

        // Post tweet
        const rwClient = client.readWrite;
        const response = await rwClient.v2.tweet(message);

        console.log('\n✅ SUCCESS! Tweet posted!');
        console.log(`🆔 Tweet ID: ${response.data.id}`);
        console.log(`🔗 URL: https://twitter.com/i/status/${response.data.id}`);

        return response.data;

    } catch (error) {
        console.error('\n❌ Failed to post tweet:');
        console.error(error.message);

        if (error.code === 403) {
            console.log('\n💡 Tip: Make sure your Twitter app has Read+Write permissions');
        }
        if (error.code === 429) {
            console.log('\n💡 Tip: Rate limited. Wait a few minutes and try again.');
        }

        process.exit(1);
    }
}

// Get message from command line
const message = process.argv.slice(2).join(' ') ||
    `Daniel FTE test post - ${new Date().toISOString().slice(0, 19)} #AIEmployee #Testing`;

postTweet(message);
