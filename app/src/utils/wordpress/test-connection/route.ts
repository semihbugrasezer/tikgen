import { NextResponse } from "next/server";
import axios from "axios";

export async function POST(request: Request) {
  try {
    const site = await request.json();
    
    // Test WordPress REST API connection
    const response = await axios.get(`${site.url}/wp-json/wp/v2/posts`, {
      auth: {
        username: site.username,
        password: site.password
      },
      timeout: 5000
    });

    return NextResponse.json({ 
      connected: true,
      version: response.headers['x-wp-total'],
      last_post: response.data[0]?.date || null
    });
  } catch (error) {
    return NextResponse.json({ 
      connected: false,
      error: "Failed to connect to WordPress site"
    }, { status: 500 });
  }
} 