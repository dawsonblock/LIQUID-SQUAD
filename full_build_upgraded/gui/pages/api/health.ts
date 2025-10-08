// Health check endpoint for Next.js
// Used by Docker health checks

import type { NextApiRequest, NextApiResponse } from 'next';

type HealthResponse = {
  ok: boolean;
  timestamp: string;
  uptime: number;
};

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse<HealthResponse>
) {
  res.status(200).json({
    ok: true,
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
}
