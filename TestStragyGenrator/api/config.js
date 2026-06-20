// Vercel serverless function: GET /api/config — non-secret env presence for UI prefill.
import { configStatus } from '../tools/mergeConfig.js';

export default function handler(_req, res) {
  res.status(200).json(configStatus());
}
