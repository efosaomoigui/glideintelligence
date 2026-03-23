import React from "react";
import Ticker from "@/components/Ticker";
import SiteHeader from "@/components/SiteHeader";
import MobileHeader from "@/components/MobileHeader";
import HeroIntelligence from "@/components/HeroIntelligence";
import DynamicIntelligence from "@/components/DynamicIntelligence";
import AIPulse from "@/components/AIPulse";
import CommunityVoices from "@/components/CommunityVoices";
import QuickPoll from "@/components/QuickPoll";
import SiteFooter from "@/components/SiteFooter";
import MobileSidebarCollapsible from "@/components/MobileSidebarCollapsible";
import SidebarAdCard from "@/components/ads/SidebarAdCard";



import { Metadata } from "next";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const metadata: Metadata = {
  title: "PAPERLY. | AI News Intelligence for West Africa",
  description: "Synthesized intelligence and contextual analysis of West African news. We don't publish news. We make sense of it.",
};

async function getHomeData() {
  try {
    const res = await fetch(`${API_URL}/api/home`, {
      cache: "no-store",
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn("Home data fetch failed:", e instanceof Error ? e.message : String(e));
  }
  return { trending_topics: [], pulse: null, voices: [] };
}

async function getSidebarData() {
  try {
    const res = await fetch(`${API_URL}/api/sidebar`, {
      cache: "no-store",
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn("Sidebar data fetch failed:", e instanceof Error ? e.message : String(e));
  }
  return { pulse: null, voices: [] };
}

const AVATAR_COLORS = ["#e74c3c", "#9b59b6", "#1abc9c", "#34495e", "#e67e22", "#2980b9", "#c0392b", "#16a085"];

function truncateText(text: string, maxChars: number = 350): string {
  if (!text || text.length <= maxChars) return text;
  const truncated = text.slice(0, maxChars);
  return truncated.slice(0, truncated.lastIndexOf(" ")) + "...";
}

export default async function Home() {
  const homeData = await getHomeData();
  const sidebarData = await getSidebarData();

  // Transform topics for DynamicIntelligence
  const initialTopics = (homeData.trending_topics || []).map((t: any) => ({
    id: String(t.id),
    title: t.title,
    slug: t.slug,
    brief: truncateText(t.ai_brief || t.description || ""),
    updatedAt: t.updated_at_str || "Recently",
    category: t.badge || t.category || "General",
    isDeveloping: t.is_trending || t.status === "developing" || (t.analysis_status && t.analysis_status !== 'complete' && t.analysis_status !== 'stable'),
    sourceCount: t.source_count || (t.sources?.length ?? 0) || 0,
    commentCount: t.engagement?.comments ?? t.comment_count ?? 0,
    viewCount: (t.engagement?.views_raw) ?? (t.view_count) ?? 0,
    sourceAvatars: (t.sources || []).slice(0, 4).map((s: any, idx: number) => ({
        initials: (s.name || "UN").substring(0, 2).toUpperCase(),
        color: AVATAR_COLORS[idx % AVATAR_COLORS.length],
    })),
  }));

  return (
    <>
      {/* Desktop Header */}
      <SiteHeader />

      {/* Mobile Header (hidden on desktop via CSS) */}
      <MobileHeader />

      {/* Ticker */}
      <Ticker />

      {/* Hero Intelligence Section */}
      <HeroIntelligence />

      {/* Dynamic Intelligence Section (includes Mobile Tabs, Feedback Grid, and Desktop Sidebar) */}
      <DynamicIntelligence initialTopics={initialTopics}>
        {/* DESKTOP SIDEBAR */}
        <aside className="sidebar">
          <AIPulse initialData={sidebarData.pulse} />
          <SidebarAdCard placement="homepage_sidebar" />
          <CommunityVoices initialData={sidebarData.voices} />
          <div className="quick-poll">
            <QuickPoll titleBelow={true} />
          </div>
        </aside>
      </DynamicIntelligence>

      {/* MOBILE SIDEBAR: stacked collapsible sections below feed */}
      <div className="mobile-sidebar-sections">
        <MobileSidebarCollapsible
          title="Intelligence Pulse"
          icon="⚡"
          defaultOpen={true}
          accent={true}
        >
          <AIPulse initialData={sidebarData.pulse} />
        </MobileSidebarCollapsible>

        <MobileSidebarCollapsible
          title="Community Voices"
          icon="💬"
          defaultOpen={false}
        >
          <CommunityVoices initialData={sidebarData.voices} />
        </MobileSidebarCollapsible>

        <MobileSidebarCollapsible
          title="Active Poll"
          icon="📊"
          defaultOpen={false}
        >
          <div className="quick-poll">
            <QuickPoll titleBelow={true} />
          </div>
        </MobileSidebarCollapsible>
      </div>

      <SiteFooter />
    </>
  );
}

