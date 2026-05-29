"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { EmailListItem } from "@/lib/types";
import { formatDate, truncate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

export default function EmailsPage() {
  const [emails, setEmails] = useState<EmailListItem[]>([]);
  const [sender, setSender] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .listEmails(1, sender || undefined)
      .then((data) => setEmails(data.items))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [sender]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Emails</h2>
          <p className="text-muted-foreground">Browse parsed emails with AI summaries</p>
        </div>
        <Input
          placeholder="Filter by sender…"
          value={sender}
          onChange={(e) => setSender(e.target.value)}
          className="max-w-xs"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Inbox</CardTitle>
          <CardDescription>{emails.length} emails loaded</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {loading &&
            Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-lg" />)}

          {!loading &&
            emails.map((email) => (
              <Link
                key={email.id}
                href={`/emails/${email.id}`}
                className="block rounded-lg border border-border p-4 transition-colors hover:border-primary/50 hover:bg-muted/30"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="font-medium">{email.subject || "(No subject)"}</h3>
                  {email.summary && <Badge variant="success">AI Summary</Badge>}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {email.sender} · {formatDate(email.sent_at)}
                </p>
                {email.summary && (
                  <p className="mt-2 text-sm text-muted-foreground">{truncate(email.summary, 180)}</p>
                )}
              </Link>
            ))}

          {!loading && !emails.length && (
            <p className="text-sm text-muted-foreground">No emails found. Upload an archive first.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
