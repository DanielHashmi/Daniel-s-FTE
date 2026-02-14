#!/usr/bin/env node
/**
 * Discord Webhook Live Post Test
 * Posts to a Discord channel via Webhook - COMPLETELY FREE, ZERO SETUP
 * 
 * Setup (2 minutes):
 * 1. Right-click any Discord channel you own
 * 2. Edit Channel → Integrations → Webhooks
 * 3. Create Webhook → Copy Webhook URL
 * 4. Paste the URL below
 * 
 * Run: node test_discord.js "Your message"
 */

const axios = require('axios');

// ==== CONFIGURE THIS ====
const WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL || 'YOUR_WEBHOOK_URL_HERE';
// ========================

async function sendDiscordMessage(message) {
    console.log('\n💬 Discord Webhook Live Post Test\n');

    if (WEBHOOK_URL === 'YOUR_WEBHOOK_URL_HERE' || !WEBHOOK_URL.includes('discord.com/api/webhooks')) {
        console.log('❌ Please configure your Discord webhook!\n');
        console.log('How to set up (2 minutes):');
        console.log('1. Open Discord and go to a server you manage');
        console.log('2. Right-click a text channel → Edit Channel');
        console.log('3. Go to Integrations → Webhooks');
        console.log('4. Click "New Webhook" or "Create Webhook"');
        console.log('5. Copy the Webhook URL');
        console.log('6. Edit this file and paste it as WEBHOOK_URL\n');
        console.log('Or set environment variable:');
        console.log('   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...');
        process.exit(1);
    }

    console.log('✓ Discord webhook configured');
    console.log(`📝 Message: "${message.substring(0, 50)}..."`);

    try {
        console.log('📤 Sending to Discord...');

        const response = await axios.post(WEBHOOK_URL, {
            content: message,
            username: 'Daniel FTE',
            avatar_url: 'https://cdn-icons-png.flaticon.com/512/4712/4712109.png'
        });

        console.log('\n✅ SUCCESS! Message posted to Discord!');
        console.log('🔗 Check your Discord channel to see it!');

    } catch (error) {
        console.error('\n❌ Failed to send message:');
        console.error(error.response?.data?.message || error.message);
        process.exit(1);
    }
}

// Get message from command line or use default
const message = process.argv.slice(2).join(' ') ||
    `🤖 **Daniel FTE - Live Demo!**\n\nThis is an automated message from my Personal AI Employee.\n\n✅ Email Management\n✅ Social Media Posting\n✅ Business Operations\n✅ 24/7 Autonomous Operation\n\n*Built for AI Employee Hackathon 2026*\n#AIEmployee #Automation`;

sendDiscordMessage(message);
