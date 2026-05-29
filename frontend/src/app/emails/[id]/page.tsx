"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { EmailDetail } from "@/lib/types";
import { formatDate, truncate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

export default function EmailDetailPage() {
  const params = useParams<{ id: string }>();
  const [email, setEmail] = useState<EmailDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!params.id) return;
    api
      .getEmail(params.id)
      .then(setEmail)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64 rounded-xl" />
      </div>
    );
  }

  if (!email) {
    return <p className="text-muted-foreground">Email not found.</p>;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Button asChild variant="ghost" className="px-0">
        <Link href="/emails">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to emails
        </Link>
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>{email.subject || "(No subject)"}</CardTitle>
          <CardDescription>
            From {email.sender} · {formatDate(email.sent_at)}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2 text-sm">
            <p>
              <span className="text-muted-foreground">To: </span>
              {email.receivers.join(", ") || "—"}
            </p>
            {email.cc.length > 0 && (
              <p>
                <span className="text-muted-foreground">Cc: </span>
                {email.cc.join(", ")}
              </p>
            )}
            {email.thread_subject && (
              <p>
                <span className="text-muted-foreground">Thread: </span>
                {email.thread_subject}
              </p>
            )}
          </div>

          <Separator />

          {email.summary && (
            <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
              <div className="mb-2 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium text-primary">AI Summary</span>
              </div>
              <p className="text-sm">{email.summary}</p>
            </div>
          )}

          <div className="whitespace-pre-wrap rounded-lg bg-muted/30 p-4 text-sm leading-relaxed">
            {email.body_text || "(Empty body)"}
          </div>
        </CardContent>
      </Card>

      {email.similar_emails.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Similar Emails</CardTitle>
            <CardDescription>ChromaDB semantic recommendations</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {email.similar_emails.map((similar) => (
              <Link
                key={similar.id}
                href={`/emails/${similar.id}`}
                className="block rounded-lg border border-border p-3 transition-colors hover:border-primary/50"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium">{similar.subject || "(No subject)"}</span>
                  <Badge variant="secondary">
                    {(similar.similarity_score * 100).toFixed(0)}% match
                  </Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {similar.sender} · {formatDate(similar.sent_at)}
                </p>
                {similar.summary && (
                  <p className="mt-2 text-sm text-muted-foreground">{truncate(similar.summary, 160)}</p>
                )}
              </Link>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
