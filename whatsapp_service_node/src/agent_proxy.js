const axios = require('axios');

const DEFAULT_AGENT_URL = 'http://localhost:8000/api/ask';

async function sendToAgent({ from, body, metadata = {} } = {}) {
  const agentUrl = process.env.AGENT_URL || DEFAULT_AGENT_URL;

  try {
    const res = await axios.post(agentUrl, {
      from,
      body,
      metadata
    }, {
      timeout: 15000
    });

    // Expect agent to return JSON with { reply: string }
    if (res && res.data) return res.data;
    return { reply: 'Sorry, no reply from agent.' };
  } catch (err) {
    console.error('Error forwarding to agent:', err && err.message || err);
    return { reply: 'Sorry, the agent is currently unavailable.' };
  }
}

module.exports = {
  sendToAgent
};
