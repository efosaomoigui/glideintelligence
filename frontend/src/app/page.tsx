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
import { adaptTopic } from "@/utils/topicAdapter";



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


export default async function Home() {
  const homeData = await getHomeData();
  const sidebarData = await getSidebarData();

  // Transform topics for DynamicIntelligence using shared adapter
  const initialTopics = (homeData.trending_topics || []).map(adaptTopic);

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

