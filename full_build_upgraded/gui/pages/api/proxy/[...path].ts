import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const { path } = req.query;
  
  if (!path || !Array.isArray(path)) {
    return res.status(400).json({ error: 'Invalid path' });
  }

  const apiPath = path.join('/');
  const url = `${API_BASE_URL}/${apiPath}`;

  try {
    const response = await axios({
      method: req.method,
      url,
      data: req.body,
      headers: {
        ...req.headers,
        host: undefined, // Remove host header to avoid conflicts
      },
      timeout: 30000,
    });

    // Forward the response
    res.status(response.status);
    
    // Set content type if available
    if (response.headers['content-type']) {
      res.setHeader('content-type', response.headers['content-type']);
    }
    
    res.send(response.data);
  } catch (error: any) {
    console.error('Proxy error:', error.message);
    
    if (error.response) {
      // Forward error response from FastAPI
      res.status(error.response.status).json(error.response.data);
    } else {
      // Network or other error
      res.status(500).json({ 
        error: 'Proxy error', 
        message: error.message 
      });
    }
  }
}