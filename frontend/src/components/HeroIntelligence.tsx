import React from "react";
import Link from "next/link";
import HeroCarousel from "./HeroCarousel"; // We will create this or put it in the same file
import { formatDistanceToNow } from "date-fns";

interface Topic {
  id: string | number;
  title: string;
  summary: string;
  bullets: string[];
  sourceCount: number;
  updatedAt: string;
  commentCount: number;
  sources: string[];
  slug: string;
  status: string;
  isPremium: boolean;
  intelligenceLevel: string;
  analysisStatus: string;
  wyntk: string[];
}

async function getHeroTopics(): Promise<Topic[]> {
  try {
    // Server-side fetch - use backend service name in Docker
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://backend:8000"}/api/home`, {
      cache: "no-store", // Ensure fresh data
    });
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error(`Failed to fetch: ${res.status} ${res.statusText}`, errorText);
      throw new Error(`Failed to fetch: ${res.status} ${res.statusText}`);
    }
    const data = await res.json();
    
    if (data && data.trending_topics) {
      return data.trending_topics.slice(0, 3).map((t: any) => {
        // Handle sources from backend - ensure it's an array of string abbreviations
        let formattedSources: string[] = [];
        if (t.sources && Array.isArray(t.sources) && t.sources.length > 0) {
            formattedSources = t.sources.map((s: any) => s.name || s.initial || s).filter(Boolean);
        } else if (t.articles) {
            formattedSources = Array.from(new Set(t.articles.map((a: any) => a.source_name))).slice(0, 4) as string[];
        }

        return {
          id: t.id,
          title: t.title,
          summary: t.ai_brief || t.description || "",
          bullets: t.bullets || t.analysis?.key_points || t.analysis?.facts || [],
          sourceCount: t.source_count || t.article_count || 0,
          updatedAt: (t.updated_at && !isNaN(new Date(t.updated_at).getTime())) 
                    ? formatDistanceToNow(new Date(t.updated_at), { addSuffix: true }) 
                    : (t.updated_at_str || "Recently"),
          commentCount: t.comment_count || 0,
          sources: formattedSources,
          slug: t.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, ""),
          status: t.badge || "DEVELOPING",
          isPremium: t.is_premium ?? false,
          intelligenceLevel: t.intelligence_level ?? "Standard",
          analysisStatus: t.analysis_status ?? "stable",
          wyntk: t.analysis?.what_you_need_to_know || t.bullets || t.analysis?.key_points || []
        };
      });
    }
    return [];
  } catch (error) {
    console.warn("Backend not running or failed to fetch hero topics:", error instanceof Error ? error.message : "Unknown error");
    return [];
  }
}

export default async function HeroIntelligence() {
  const topics = await getHeroTopics();

  if (!topics || topics.length === 0) return null;

  return <HeroCarousel topics={topics} />;
}
