"use client";

import { useCallback, useEffect, useState } from "react";
import { FileArchive, Loader2, UploadCloud } from "lucide-react";
import { api } from "@/lib/api";
import type { Archive } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

const statusVariant: Record<Archive["status"], "warning" | "default" | "success" | "destructive"> = {
  pending: "warning",
  processing: "default",
  completed: "success",
  failed: "destructive",
};

export default function UploadPage() {
  const [archives, setArchives] = useState<Archive[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadArchives = useCallback(async () => {
    const data = await api.listArchives();
    setArchives(data.items);
  }, []);

  useEffect(() => {
    loadArchives().catch(console.error);
    const interval = setInterval(() => {
      loadArchives().catch(console.error);
    }, 5000);
    return () => clearInterval(interval);
  }, [loadArchives]);

  async function handleUpload(file: File) {
    if (!file.name.toLowerCase().endsWith(".zip")) {
      setError("Only .zip archives are supported.");
      return;
    }

    setUploading(true);
    setError(null);
    setMessage(null);

    try {
      const result = await api.uploadArchive(file);
      setMessage(result.message);
      await loadArchives();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function onDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file) void handleUpload(file);
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Upload Archive</h2>
        <p className="text-muted-foreground">
          Upload ZIP email exports for parsing, indexing, embedding, and AI summarization.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>ZIP Email Archive</CardTitle>
          <CardDescription>Drag and drop or browse for a .zip file containing .eml exports</CardDescription>
        </CardHeader>
        <CardContent>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-colors ${
              dragOver ? "border-primary bg-primary/5" : "border-border"
            }`}
          >
            <UploadCloud className="mb-4 h-12 w-12 text-primary" />
            <p className="mb-4 text-sm text-muted-foreground">Drop your ZIP archive here</p>
            <label>
              <input
                type="file"
                accept=".zip"
                className="hidden"
                disabled={uploading}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void handleUpload(file);
                }}
              />
              <Button asChild disabled={uploading}>
                <span>{uploading ? "Uploading…" : "Browse Files"}</span>
              </Button>
            </label>
            {uploading && <Loader2 className="mt-4 h-5 w-5 animate-spin text-primary" />}
          </div>

          {message && <p className="mt-4 text-sm text-emerald-400">{message}</p>}
          {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent Uploads</CardTitle>
          <CardDescription>Processing status refreshes every 5 seconds</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {archives.map((archive) => {
            const progress =
              archive.total_emails > 0
                ? Math.round((archive.processed_emails / archive.total_emails) * 100)
                : archive.status === "completed"
                  ? 100
                  : 0;

            return (
              <div key={archive.id} className="rounded-lg border border-border p-4">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <FileArchive className="h-4 w-4 text-primary" />
                    <span className="font-medium">{archive.filename}</span>
                  </div>
                  <Badge variant={statusVariant[archive.status]}>{archive.status}</Badge>
                </div>
                <Progress value={progress} className="mb-2" />
                <div className="flex flex-wrap justify-between gap-2 text-xs text-muted-foreground">
                  <span>
                    {archive.processed_emails}/{archive.total_emails} emails processed
                  </span>
                  <span>{formatDate(archive.created_at)}</span>
                </div>
                {archive.error_message && (
                  <p className="mt-2 text-xs text-red-400">{archive.error_message}</p>
                )}
              </div>
            );
          })}
          {!archives.length && (
            <p className="text-sm text-muted-foreground">No archives uploaded yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
