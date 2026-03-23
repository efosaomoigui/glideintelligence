import { Metadata } from "next";
import CategoryClient from "@/components/CategoryClient";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const VERTICAL_CONFIGS: Record<string, any> = {
  economy: {
    name: "Economy",
    icon: "💰",
    color: "#2980b9",
    description: "Glide-synthesized analysis of Nigeria's economic landscape—from currency movements and monetary policy to fiscal reforms and market dynamics.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "ECONOMY",
    insights: [],
    trending: [],
    newsletterTitle: "Daily Economy Brief",
    newsletterDesc: "Get PAPERLY.-synthesized economic intelligence in your inbox every morning at 6 AM WAT.",
  },
  politics: {
    name: "Politics",
    icon: "🏛️",
    color: "#8e44ad",
    description: "In-depth intelligence on Nigeria's political landscape—tracking legislative battles, executive actions, and party dynamics.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "POLITICS",
    insights: [],
    trending: [],
    newsletterTitle: "Daily Politics Brief",
    newsletterDesc: "Stay ahead of Nigeria's political developments with our PAPERLY.-curated morning brief.",
  },
  business: {
    name: "Business",
    icon: "🏢",
    color: "#16a085",
    description: "Enterprise intelligence covering Nigerian and West African business — startup ecosystems, corporate strategy, and trade flows.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "BUSINESS",
    insights: [],
    trending: [],
    newsletterTitle: "Daily Business Brief",
    newsletterDesc: "Business intelligence for West Africa's decision-makers — delivered at 6 AM WAT.",
  },
  security: {
    name: "Security",
    icon: "🛡️",
    color: "#c0392b",
    description: "Critical intelligence on security threats, military operations, and public safety across Nigeria and the West African region.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "SECURITY",
    insights: [],
    trending: [],
    newsletterTitle: "Security Intelligence Brief",
    newsletterDesc: "Critical security updates synthesized daily for informed situational awareness.",
  },
  technology: {
    name: "Technology",
    icon: "💻",
    color: "#27ae60",
    description: "Intelligence on Nigeria's growing tech ecosystem — fintech, AI policy, telecom regulation, and the digital economy.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "TECHNOLOGY",
    insights: [],
    trending: [],
    newsletterTitle: "Tech Intelligence Brief",
    newsletterDesc: "Daily digest of Nigeria's technology sector — policy, investment, and innovation.",
  },
  regional: {
    name: "Regional",
    icon: "🌍",
    color: "#d97706",
    description: "West African regional intelligence — ECOWAS dynamics, cross-border trade, and regional security cooperation.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "REGIONAL",
    insights: [],
    trending: [],
    newsletterTitle: "Regional Intelligence Brief",
    newsletterDesc: "West Africa regional analysis delivered every morning — stay regionally informed.",
  },
  "global-impact": {
    name: "Global Impact",
    icon: "🌐",
    color: "#2c3e50",
    description: "How global macro trends — US policy, China-Africa dynamics, and commodity markets — affect Nigeria and West Africa.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "GLOBAL",
    insights: [],
    trending: [],
    newsletterTitle: "Global Impact Brief",
    newsletterDesc: "How the world affects your economy — synthesised daily for decision-makers.",
  },
  "sport": {
    name: "Sport",
    icon: "⚽",
    color: "#e67e22",
    description: "PAPERLY.-synthesized analysis of Nigerian and international sports — tracking football, local leagues, and athlete performances.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "SPORT",
    insights: [],
    trending: [],
    newsletterTitle: "Daily Sport Brief",
    newsletterDesc: "The intelligence behind the game — delivered every morning at 6 AM WAT.",
  },
};

export async function generateMetadata({ params }: { params: Promise<{ category: string }> }): Promise<Metadata> {
  const resolvedParams = await params;
  const category = resolvedParams.category || "economy";
  const capitalized = category.charAt(0).toUpperCase() + category.slice(1);
  
  return {
    title: `${capitalized} Intelligence | PAPERLY.`,
    description: `Expert news synthesis and intelligence on ${capitalized} in Nigeria and West Africa.`,
    alternates: {
      canonical: `/${category.toLowerCase()}`,
      languages: {
        "en-NG": `/${category.toLowerCase()}`,
        "en": `/${category.toLowerCase()}`,
        "x-default": `/${category.toLowerCase()}`,
      },
    },
    openGraph: {
      title: `${capitalized} News & Analysis | PAPERLY. Intelligence`,
      description: `In-depth analysis of ${capitalized} developments across the region.`,
    }
  };
}

async function getCategoryData(categorySlug: string) {
  try {
    const res = await fetch(`${API_URL}/api/vertical/${encodeURIComponent(categorySlug)}`, {
      next: { revalidate: 300 }
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn("Category fetch failed on server:", e instanceof Error ? e.message : String(e));
  }
  return { topics: [], pulse: null, stats: null };
}

export default async function CategoryPage({ params }: { params: Promise<{ category: string }> }) {
  const resolvedParams = await params;
  const categorySlug = resolvedParams.category || "economy";
  const initialData = await getCategoryData(categorySlug);
  const config = VERTICAL_CONFIGS[categorySlug] || VERTICAL_CONFIGS["economy"];

  return (
    <CategoryClient 
      categorySlug={categorySlug} 
      initialData={initialData} 
      config={config} 
    />
  );
}
