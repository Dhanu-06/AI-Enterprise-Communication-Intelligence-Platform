"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, ArrowRight, Mail, Network, Users } from "lucide-react";
import { api } from "@/lib/api";
import type { AnalyticsDashboard, HealthResponse } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.health(), api.getAnalytics()])
      .then(([healthData, analyticsData]) => {
        setHealth(healthData);
        setAnalytics(analyticsData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-xl" />
        ))}
      </div>
    );
  }

  const overview = analytics?.overview;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">
            Communication intelligence overview across PostgreSQL, Elasticsearch, and ChromaDB.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link href="/upload">Upload Archive</Link>
          </Button>
          <Button asChild>
            <Link href="/search">
              Search Emails <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Mail} label="Total Emails" value={overview?.total_emails ?? 0} />
        <StatCard icon={Network} label="Threads" value={overview?.total_threads ?? 0} />
        <StatCard icon={Users} label="Unique Senders" value={overview?.unique_senders ?? 0} />
        <StatCard icon={Activity} label="With AI Summary" value={overview?.emails_with_summary ?? 0} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>System Health</CardTitle>
            <CardDescription>Live status of platform services</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            <HealthBadge label="API" status={health?.status ?? "unknown"} />
            <HealthBadge label="PostgreSQL" status={health?.database?.status ?? "unknown"} />
            <HealthBadge label="Elasticsearch" status={health?.elasticsearch?.status ?? "unknown"} />
            <HealthBadge label="ChromaDB" status={health?.chromadb?.status ?? "unknown"} />
            <HealthBadge
              label="ES Documents"
              status={String(health?.elasticsearch?.document_count ?? 0)}
              variant="secondary"
            />
            <HealthBadge
              label="Vector Count"
              status={String(health?.chromadb?.document_count ?? 0)}
              variant="secondary"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Senders</CardTitle>
            <CardDescription>Most active communicators</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(analytics?.top_senders ?? []).slice(0, 5).map((item) => (
              <div key={item.sender} className="flex items-center justify-between text-sm">
                <span className="truncate text-muted-foreground">{item.sender}</span>
                <Badge variant="secondary">{item.count}</Badge>
              </div>
            ))}
            {!analytics?.top_senders?.length && (
              <p className="text-sm text-muted-foreground">Upload an archive to see analytics.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <Icon className="h-4 w-4 text-primary" />
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold">{value.toLocaleString()}</div>
      </CardContent>
    </Card>
  );
}

function HealthBadge({
  label,
  status,
  variant = "outline",
}: {
  label: string;
  status: string;
  variant?: "outline" | "secondary";
}) {
  const isOk = ["ok", "connected"].includes(status);
  return (
    <div className="rounded-lg border border-border p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <Badge variant={variant === "secondary" ? "secondary" : isOk ? "success" : "warning"} className="mt-2">
        {status}
      </Badge>
    </div>
  );
}
