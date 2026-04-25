const AGENTSHERIFF_GATEWAY_URL =
  process.env.AGENTSHERIFF_GATEWAY_URL ?? "http://127.0.0.1:8000";

const VALID_ACTIONS = new Set(["approve", "deny", "redact"]);

async function handleCallback(ctx) {
  const payload = ctx?.callback?.payload ?? "";
  const colon = payload.indexOf(":");
  if (colon < 0) return { handled: false };

  const action = payload.slice(0, colon);
  const approvalId = payload.slice(colon + 1);
  if (!VALID_ACTIONS.has(action) || !approvalId) {
    return { handled: false };
  }

  let resolveOk = false;
  try {
    const resp = await fetch(
      `${AGENTSHERIFF_GATEWAY_URL}/v1/approvals/${approvalId}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      },
    );
    resolveOk = resp.ok;
    if (!resp.ok) {
      const body = await resp.text().catch(() => "");
      console.error(
        `[agentsheriff-telegram-callbacks] resolve ${approvalId} failed: ${resp.status} ${body}`,
      );
    }
  } catch (err) {
    console.error("[agentsheriff-telegram-callbacks] fetch error:", err);
  }

  // Delete the request message so the user gets immediate feedback.
  try {
    await ctx.respond.deleteMessage();
  } catch {
    // already gone — ignore
  }

  if (!resolveOk) {
    try {
      await ctx.respond.reply({
        text: "AgentSheriff gateway unreachable — approval not resolved.",
      });
    } catch {
      // ignore
    }
  }

  return { handled: true };
}

const plugin = {
  id: "agentsheriff-telegram-callbacks",
  name: "AgentSheriff Telegram Callbacks",
  description:
    "Forward Telegram approval button taps (namespace 'agentsheriff') to the AgentSheriff gateway.",
  register(api) {
    api.registerInteractiveHandler({
      channel: "telegram",
      namespace: "agentsheriff",
      handler: handleCallback,
    });
  },
};

export default plugin;
