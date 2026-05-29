"use client";

import { useState } from "react";
import Link from "next/link";
import { Loader2, Search, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { SearchHit } from "@/lib/types";
import { formatDate, truncate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

export default function SearchPage() {
  const [keywordQuery, setKeywordQuery] = useState("");
  const [semanticQuery, setSemanticQuery] = useState("");
  const [keywordResults, setKeywordResults] = useState<SearchHit[]>([]);
  const [semanticResults, setSemanticResults] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState<"keyword" | "semantic" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function runKeywordSearch() {
    if (!keywordQuery.trim()) return;
    setLoading("keyword");
    setError(null);
    try {
      const data = await api.keywordSearch(keywordQuery.trim());
      setKeywordResults(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Keyword search failed");
    } finally {
      setLoading(null);
    }
  }

  async function runSemanticSearch() {
    if (!semanticQuery.trim()) return;
    setLoading("semantic");
    setError(null);
    try {
      const data = await api.semanticSearch(semanticQuery.trim());
      setSemanticResults(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Semantic search failed");
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Search</h2>
        <p className="text-muted-foreground">
          Keyword search via Elasticsearch or semantic search via ChromaDB embeddings.
        </p>
      </div>

      <Tabs defaultValue="semantic">
        <TabsList>
          <TabsTrigger value="semantic">
            <Sparkles className="mr-2 h-4 w-4" /> Semantic Search
          </TabsTrigger>
          <TabsTrigger value="keyword">
            <Search className="mr-2 h-4 w-4" /> Keyword Search
          </TabsTrigger>
        </TabsList>

        <TabsContent value="semantic">
          <Card>
            <CardHeader>
              <CardTitle>Semantic Search</CardTitle>
              <CardDescription>
                Find emails by meaning using ChromaDB vector similarity (recommended).
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="e.g. emails about Q1 planning milestones and deliverables"
                value={semanticQuery}
                onChange={(e) => setSemanticQuery(e.target.value)}
                rows={4}
              />
              <Button onClick={runSemanticSearch} disabled={loading === "semantic"}>
                {loading === "semantic" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                Search Semantically
              </Button>
              <ResultsList results={semanticResults} scoreLabel="Similarity" />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="keyword">
          <Card>
            <CardHeader>
              <CardTitle>Keyword Search</CardTitle>
              <CardDescription>Full-text search powered by Elasticsearch</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Search subject, body, sender…"
                  value={keywordQuery}
                  onChange={(e) => setKeywordQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && runKeywordSearch()}
                />
                <Button onClick={runKeywordSearch} disabled={loading === "keyword"}>
                  {loading === "keyword" ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                  Search
                </Button>
              </div>
              <ResultsList results={keywordResults} scoreLabel="Relevance" />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {error && <p className="text-sm text-red-400">{error}</p>}
    </div>
  );
}

function ResultsList({ results, scoreLabel }: { results: SearchHit[]; scoreLabel: string }) {
  if (!results.length) {
    return <p className="text-sm text-muted-foreground">No results yet.</p>;
  }

  return (
    <div className="space-y-3">
      {results.map((hit) => (
        <Link
          key={hit.id}
          href={`/emails/${hit.id}`}
          className="block rounded-lg border border-border p-4 transition-colors hover:border-primary/50 hover:bg-muted/30"
        >
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-medium">{hit.subject || "(No subject)"}</h3>
            <Badge variant="secondary">
              {scoreLabel}: {(hit.score * (scoreLabel === "Similarity" ? 100 : 1)).toFixed(scoreLabel === "Similarity" ? 0 : 2)}
              {scoreLabel === "Similarity" ? "%" : ""}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            {hit.sender} · {formatDate(hit.sent_at)}
          </p>
          <p className="mt-2 text-sm text-muted-foreground">{truncate(hit.snippet || hit.summary || "", 220)}</p>
        </Link>
      ))}
    </div>
  );
}
