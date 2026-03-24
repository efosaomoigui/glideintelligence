import { formatDistanceToNow } from "date-fns";

export interface Perspective {
  source: string;
  sentiment: "positive" | "negative" | "neutral";
  score: number;
}

export interface ImpactItem {
  icon: string;
  title: string;
  value: string;
}

export interface SourceAvatar {
  initials: string;
  color: string;
}

export interface AdaptedTopic {
  id: string;
  title: string;
  category: string;
  region?: string | null;
  isDeveloping?: boolean;
  updatedAt: string;
  brief: string;
  perspectives: Perspective[];
  impacts: ImpactItem[];
  sourceAvatars: SourceAvatar[];
  sourceCount: number;
  commentCount: number;
  viewCount: number;
  isPremium?: boolean;
  intelligenceLevel?: string;
  analysisStatus?: string;
  slug?: string;
  seeMore?: boolean;
  hasSocialReactions?: boolean;
}

const AVATAR_COLORS = ["#e74c3c", "#9b59b6", "#1abc9c", "#34495e", "#e67e22", "#2980b9", "#c0392b", "#16a085"];

export function truncateText(text: string, maxChars: number = 350): string {
  if (!text || text.length <= maxChars) return text;
  const truncated = text.slice(0, maxChars);
  const lastSpace = truncated.lastIndexOf(" ");
  return (lastSpace > 0 ? truncated.slice(0, lastSpace) : truncated) + "...";
}

export function getSafeRelativeTime(dateStr: string, fallbackStr: string): string {
  if (!dateStr) return fallbackStr || "Recently";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return fallbackStr || "Recently";
    return formatDistanceToNow(d, { addSuffix: true });
  } catch {
    return fallbackStr || "Recently";
  }
}

export function adaptTopic(t: any): AdaptedTopic {
  // Normalize perspectives
  const rawPerspectives = t.source_perspectives || t._perspectives_data || [];
  const perspectives: Perspective[] = rawPerspectives.map((p: any) => {
    let score = 0;
    if (typeof p.sentiment_percentage === "string") {
      score = parseInt(p.sentiment_percentage.replace("%", "").replace("+", "")) || 0;
    } else if (typeof p.sentiment_percentage === "number") {
      score = p.sentiment_percentage;
    } else if (typeof p.sentiment_score === "number") {
      score = p.sentiment_score * 100;
    }

    return {
      source: p.source_name || p.frame_label || "Source",
      sentiment: (p.sentiment || "neutral") as "positive" | "negative" | "neutral",
      score,
    };
  });

  // Normalize impacts
  const rawImpacts = t.regional_impacts || t._impacts_data || [];
  const impacts: ImpactItem[] = rawImpacts.map((imp: any) => ({
    icon: imp.icon || "📊",
    title: imp.title || imp.impact_category || "Impact",
    value: imp.value || imp.context || "",
  }));

  // Normalize source avatars
  const sourceAvatars: SourceAvatar[] = (t.sources || []).map((s: any, idx: number) => ({
    initials: (s.name || s.initial || "UN").substring(0, 2).toUpperCase(),
    color: s.bg || s.color || AVATAR_COLORS[idx % AVATAR_COLORS.length],
  }));

  const updatedAt = t.updated_at_str || (t.updated_at ? getSafeRelativeTime(t.updated_at, "Recently") : "Recently");

  return {
    id: String(t.id),
    title: t.title || "Untitled Topic",
    slug: t.slug || (t.title ? t.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") : ""),
    category: t.category || t.badge || "General",
    region: t.region_name || t.region || null,
    isDeveloping: t.is_trending || t.status === "developing" || (t.analysis_status && t.analysis_status !== 'complete' && t.analysis_status !== 'stable'),
    updatedAt,
    brief: truncateText(t.ai_brief || t.description || "", 350),
    perspectives: perspectives.length ? perspectives : [
      { source: "Nigerian Media", sentiment: "positive", score: 75 },
      { source: "International", sentiment: "neutral", score: 50 },
      { source: "Social Media", sentiment: "neutral", score: 45 },
    ],
    impacts: impacts.length ? impacts : [
      { icon: "📊", title: "Analysis", value: "Intelligence synthesis in progress" },
    ],
    sourceAvatars: sourceAvatars.length ? sourceAvatars : [
      { initials: "GL", color: "#e74c3c" },
    ],
    sourceCount: t.source_count || (t.sources?.length ?? 0) || 1,
    commentCount: t.engagement?.comments ?? t.comment_count ?? 0,
    viewCount: (t.engagement?.views_raw) ?? (t.view_count) ?? 0,
    isPremium: Boolean(t.is_premium) || t.intelligence_level === "Premium",
    intelligenceLevel: t.intelligence_level || "Standard",
    analysisStatus: t.analysis_status || "stable",
    seeMore: true,
    hasSocialReactions: (t.social_reactions && t.social_reactions.length > 0) || Boolean(t.has_social_reactions)
  };
}
