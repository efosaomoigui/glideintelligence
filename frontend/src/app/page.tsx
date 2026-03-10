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



export default function Home() {
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
      <DynamicIntelligence>
        {/* DESKTOP SIDEBAR */}
        <aside className="sidebar">
          <AIPulse />
          <SidebarAdCard />
          <CommunityVoices />
          <QuickPoll />
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
          <AIPulse />
        </MobileSidebarCollapsible>

        <MobileSidebarCollapsible
          title="Community Voices"
          icon="💬"
          defaultOpen={false}
        >
          <CommunityVoices />
        </MobileSidebarCollapsible>

        <MobileSidebarCollapsible
          title="Active Poll"
          icon="📊"
          defaultOpen={false}
        >
          <QuickPoll />
        </MobileSidebarCollapsible>
      </div>

      <SiteFooter />
    </>
  );
}
