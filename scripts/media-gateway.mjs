#!/usr/bin/env node
// Opt-in media gateway: dry-run by default. No paid calls without two explicit gates.
import process from "node:process";

const argv = process.argv.slice(2);
const option = (name) => {
  const index = argv.indexOf(name);
  return index >= 0 ? argv[index + 1] : undefined;
};
const provider = option("--provider");
const model = option("--model");
const prompt = option("--prompt");
const execute = argv.includes("--execute");

async function main() {
  if (!["fal", "higgsfield"].includes(provider) || !model || !prompt) {
    throw new Error("Usage: node scripts/media-gateway.mjs --provider fal|higgsfield --model PROVIDER_MODEL --prompt TEXT [--execute]");
  }
  if (!/^[a-zA-Z0-9._/-]+$/.test(model) || model.includes("..") || model.startsWith("/")) {
    throw new Error("Invalid model path");
  }
  if (!execute) {
    console.log(JSON.stringify({ status: "dry-run", provider, model, promptLength: prompt.length, networkCalls: 0, billableCalls: 0 }, null, 2));
    return;
  }
  if (process.env.ALLOW_PAID_MEDIA !== "YES") {
    throw new Error("Blocked: --execute also requires ALLOW_PAID_MEDIA=YES and active provider credentials");
  }
  if (provider === "fal") {
    if (!process.env.FAL_KEY) throw new Error("FAL_KEY is missing");
    let fal;
    try {
      ({ fal } = await import("@fal-ai/client"));
    } catch {
      throw new Error("Install official @fal-ai/client in this workspace before use");
    }
    fal.config({ credentials: process.env.FAL_KEY });
    const result = await fal.subscribe(model, { input: { prompt } });
    console.log(JSON.stringify({ provider, status: "completed", requestId: result.requestId ?? null }));
    return;
  }
  const id = process.env.HF_API_KEY_ID;
  const secret = process.env.HF_API_KEY_SECRET;
  if (!id || !secret) throw new Error("HF_API_KEY_ID and HF_API_KEY_SECRET are required");
  // Payload shape is a starting point for the documented Seedance text-to-video endpoint.
  // Check the selected model's exact schema before a paid execution.
  const input = { prompt, resolution: "720p", generate_audio: false, duration: 5, aspect_ratio: "16:9" };
  const response = await fetch("https://api.higgsfield.ai/" + model, {
    method: "POST",
    headers: { "Authorization": "Key " + id + ":" + secret, "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) throw new Error("Higgsfield HTTP " + response.status + " (response body hidden)");
  const payload = await response.json();
  console.log(JSON.stringify({ provider, status: "submitted", requestId: payload.id ?? payload.request_id ?? null }));
}

main().catch((error) => {
  console.error("Media gateway: " + error.message);
  process.exitCode = 1;
});
