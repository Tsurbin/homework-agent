require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const { MessagingResponse } = require('twilio').twiml;
const { sendToAgent } = require('./agent_proxy');

const app = express();
const PORT = process.env.PORT || 3000;

// Twilio sends application/x-www-form-urlencoded for webhook messages
app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());

// Health
app.get('/health', (req, res) => res.json({ status: 'ok', service: 'whatsapp_node' }));

// Test API - accepts JSON { from, body }
app.post('/api/message', async (req, res) => {
  const { from, body } = req.body;
  if (!body) return res.status(400).json({ error: 'body is required' });

  const result = await sendToAgent({ from, body });
  return res.json(result);
});

// Twilio webhook for incoming WhatsApp messages
app.post('/webhook', async (req, res) => {
  const incomingBody = req.body.Body || req.body.body || '';
  const from = req.body.From || req.body.from || 'unknown';

  console.log('[webhook] message from', from, ':', incomingBody);

  const agentResult = await sendToAgent({ from, body: incomingBody });
  const replyText = (agentResult && (agentResult.reply || agentResult.text)) || 'Sorry, I have no answer right now.';

  // Build TwiML response
  const twiml = new MessagingResponse();
  twiml.message(replyText);

  res.type('text/xml').send(twiml.toString());
});

app.listen(PORT, () => {
  console.log(`WhatsApp Node service listening on port ${PORT}`);
  console.log(`Webhook endpoint: POST /webhook`);
  console.log(`Agent forwarding to: ${process.env.AGENT_URL || 'http://localhost:8000/api/ask'}`);
});
