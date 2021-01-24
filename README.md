# factorio_bot
A Slack app that sends server activity notifications to a channel

 - Configure the Factorio headless server to listen to RCON requests: https://wiki.factorio.com/Command_line_parameters (see --rcon-port/bind/password); please use a strong password, and bind to localhost if this script is going to be running on the same machine;
 - Configure a Slack app and set up an Incoming Webhook as described here: https://api.slack.com/messaging/webhooks#posting_with_webhooks ; the resulting URL will let your app post into a channel without further authentication. The URL should be kept secret, don't publish it on github/pastebin/etc.
 - Install required packages: pip install -r requirements.txt
 - Copy sample_config.json -> config.json, add RCON parameters and the Slack webhook URL to config.json and run bot.py.

TODO: Telegram, Discord
