#!/usr/bin/env node
/**
 * Telegram Live Post Test
 * Posts to a Telegram channel/chat via Bot API - COMPLETELY FREE
 * 
 * Setup:
 * 1. Message @BotFather on Telegram, send /newbot
 * 2. Copy the bot token
 * 3. Start a chat with your bot OR add it to a channel
 * 4. Get your chat_id (message the bot, then check getUpdates)
 * 
 * Run: node test_telegram.js "Your message"
 */

const axios = require('axios');

// ==== CONFIGURE THESE ====
const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || 'YOUR_BOT_TOKEN_HERE';
const CHAT_ID = process.env.TELEGRAM_CHAT_ID || 'YOUR_CHAT_ID_HERE';
// =========================

async function sendTelegramMessage(message) {
    console.log('\n📱 Telegram Live Post Test\n');

    if (BOT_TOKEN === 'YOUR_BOT_TOKEN_HERE' || CHAT_ID === 'YOUR_CHAT_ID_HERE') {
        console.log('❌ Please configure your Telegram credentials!\n');
        console.log('How to set up (5 minutes):');
        console.log('1. Open Telegram and search for @BotFather');
        console.log('2. Send /newbot and follow the prompts');
        console.log('3. Copy the bot token (looks like: 123456:ABC-DEF1234...)');
        console.log('4. Start a chat with your bot (search for it and click Start)');
        console.log('5. To get your chat_id, visit:');
        console.log(`   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`);
        console.log('6. Edit this file and paste your BOT_TOKEN and CHAT_ID\n');
        console.log('Or set environment variables:');
        console.log('   TELEGRAM_BOT_TOKEN=your_token');
        console.log('   TELEGRAM_CHAT_ID=your_chat_id');
        process.exit(1);
    }

    console.log('✓ Telegram credentials configured');
    console.log(`📝 Message: "${message}"`);
    console.log(`📏 Length: ${message.length} characters\n`);

    try {
        const url = `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`;

        console.log('📤 Sending to Telegram...');

        const response = await axios.post(url, {
            chat_id: CHAT_ID,
            text: message,
            parse_mode: 'HTML'
        });

        if (response.data.ok) {
            console.log('\n✅ SUCCESS! Message sent to Telegram!');
            console.log(`🆔 Message ID: ${response.data.result.message_id}`);
            console.log(`📅 Sent at: ${new Date(response.data.result.date * 1000).toISOString()}`);
            return response.data.result;
        } else {
            throw new Error(response.data.description);
        }

    } catch (error) {
        console.error('\n❌ Failed to send message:');
        console.error(error.response?.data?.description || error.message);
        process.exit(1);
    }
}

// Get message from command line or use default
const message = process.argv.slice(2).join(' ') ||
    `🤖 <b>Daniel FTE</b> - Testing Live!\n\nThis is an automated message from my AI Employee.\n\n#AIEmployee #Automation #Hackathon2026`;

sendTelegramMessage(message);
