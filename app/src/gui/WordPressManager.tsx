"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle2, XCircle, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

interface WordPressSite {
  url: string;
  username: string;
  password: string;
  category: string;
  post_interval: string;
  max_posts_per_day: string;
  is_connected?: boolean;
  last_post?: string;
  next_post?: string;
}

export function WordPressManager() {
  const [sites, setSites] = useState<WordPressSite[]>([]);
  const [loading, setLoading] = useState(false);
  const [newSite, setNewSite] = useState<WordPressSite>({
    url: "",
    username: "",
    password: "",
    category: "technology",
    post_interval: "6",
    max_posts_per_day: "4"
  });

  useEffect(() => {
    loadSites();
  }, []);

  const loadSites = async () => {
    try {
      const response = await fetch("/api/wordpress/sites");
      const data = await response.json();
      setSites(data);
    } catch (error) {
      toast.error("Failed to load WordPress sites");
    }
  };

  const testConnection = async (site: WordPressSite) => {
    try {
      const response = await fetch("/api/wordpress/test-connection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(site)
      });
      const data = await response.json();
      return data.connected;
    } catch (error) {
      return false;
    }
  };

  const addSite = async () => {
    if (!newSite.url || !newSite.username || !newSite.password) {
      toast.error("Please fill in all required fields");
      return;
    }

    setLoading(true);
    try {
      const isConnected = await testConnection(newSite);
      const updatedSites = [...sites, { ...newSite, is_connected: isConnected }];
      setSites(updatedSites);
      setNewSite({
        url: "",
        username: "",
        password: "",
        category: "technology",
        post_interval: "6",
        max_posts_per_day: "4"
      });
      toast.success("WordPress site added successfully");
    } catch (error) {
      toast.error("Failed to add WordPress site");
    } finally {
      setLoading(false);
    }
  };

  const removeSite = async (url: string) => {
    try {
      const updatedSites = sites.filter(site => site.url !== url);
      setSites(updatedSites);
      toast.success("WordPress site removed successfully");
    } catch (error) {
      toast.error("Failed to remove WordPress site");
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Add New WordPress Site</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="url">Site URL</Label>
              <Input
                id="url"
                placeholder="https://example.com"
                value={newSite.url}
                onChange={(e) => setNewSite({ ...newSite, url: e.target.value })}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                placeholder="admin"
                value={newSite.username}
                onChange={(e) => setNewSite({ ...newSite, username: e.target.value })}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={newSite.password}
                onChange={(e) => setNewSite({ ...newSite, password: e.target.value })}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="category">Category</Label>
              <Input
                id="category"
                placeholder="technology"
                value={newSite.category}
                onChange={(e) => setNewSite({ ...newSite, category: e.target.value })}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="post_interval">Post Interval (hours)</Label>
              <Input
                id="post_interval"
                type="number"
                value={newSite.post_interval}
                onChange={(e) => setNewSite({ ...newSite, post_interval: e.target.value })}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="max_posts">Max Posts Per Day</Label>
              <Input
                id="max_posts"
                type="number"
                value={newSite.max_posts_per_day}
                onChange={(e) => setNewSite({ ...newSite, max_posts_per_day: e.target.value })}
              />
            </div>
            <Button onClick={addSite} disabled={loading}>
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
              Add Site
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Connected WordPress Sites</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sites.map((site) => (
              <Card key={site.url}>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{site.url}</h3>
                        {site.is_connected ? (
                          <Badge variant="success">
                            <CheckCircle2 className="mr-1 h-3 w-3" />
                            Connected
                          </Badge>
                        ) : (
                          <Badge variant="destructive">
                            <XCircle className="mr-1 h-3 w-3" />
                            Disconnected
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Category: {site.category} | Posts: {site.max_posts_per_day}/day
                      </p>
                      {site.last_post && (
                        <p className="text-sm text-muted-foreground">
                          Last post: {new Date(site.last_post).toLocaleString()}
                        </p>
                      )}
                      {site.next_post && (
                        <p className="text-sm text-muted-foreground">
                          Next post: {new Date(site.next_post).toLocaleString()}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeSite(site.url)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
            {sites.length === 0 && (
              <p className="text-center text-muted-foreground">
                No WordPress sites added yet
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 