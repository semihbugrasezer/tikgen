import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const configPath = path.join(process.cwd(), "config.json");

export async function GET() {
  try {
    const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
    return NextResponse.json(config.wordpress_sites || []);
  } catch (error) {
    return NextResponse.json({ error: "Failed to load WordPress sites" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const site = await request.json();
    const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
    
    if (!config.wordpress_sites) {
      config.wordpress_sites = [];
    }

    // Check if site already exists
    const existingIndex = config.wordpress_sites.findIndex((s: any) => s.url === site.url);
    if (existingIndex !== -1) {
      config.wordpress_sites[existingIndex] = site;
    } else {
      config.wordpress_sites.push(site);
    }

    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to save WordPress site" }, { status: 500 });
  }
}

export async function DELETE(request: Request) {
  try {
    const { url } = await request.json();
    const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
    
    if (config.wordpress_sites) {
      config.wordpress_sites = config.wordpress_sites.filter((site: any) => site.url !== url);
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to delete WordPress site" }, { status: 500 });
  }
} 