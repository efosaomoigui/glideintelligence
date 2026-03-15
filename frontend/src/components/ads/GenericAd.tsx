"use client";

import React, { useEffect, useRef, useState } from "react";
import Image from "next/image";

interface AdExternalNetwork {
  network_name: string;
  ad_size?: string;
  script_code: string;
}

interface AdSponsor {
  tagline?: string;
  summary?: string;
  full_content?: string;
  image_url?: string;
  cta_text: string;
  website_link?: string;
}

interface AdImage {
  image_url: string;
  target_url: string;
  alt_text?: string;
  ad_size?: string;
}

export interface AdData {
  id: string;
  ad_type: "external" | "sponsor" | "image";
  title: string;
  placement_group: string;
  external?: AdExternalNetwork;
  sponsor?: AdSponsor;
  image?: AdImage;
}

interface GenericAdProps {
  ad: AdData;
  onSponsorClick?: (ad: AdData) => void;
}

// Declared before GenericAd so it's in scope when GenericAd references it.
// In-feed Sponsored Content card — styled like an intelligence card.
// Dismiss uses component state only → resets on every page refresh (by design).
function DismissableSponsored({
  ad,
  onSponsorClick,
  containerRef,
}: {
  ad: AdData;
  onSponsorClick?: (ad: AdData) => void;
  containerRef: React.RefObject<HTMLDivElement | null>;
}) {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed) return null;

  const openFlyout = () => {
    if (onSponsorClick) {
      onSponsorClick(ad);
    } else {
      window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "sponsor", ...ad } }));
    }
  };

  return (
    <div
      ref={containerRef}
      style={{
        margin: "0",
        position: "relative",
        borderRadius: "12px",
        background: "rgba(15,17,24,0.85)",
        border: "1px solid rgba(59,130,246,0.2)",
        backdropFilter: "blur(6px)",
        overflow: "hidden",
        transition: "border-color 0.2s, box-shadow 0.2s",
        cursor: "pointer",
        boxShadow: "0 2px 16px rgba(0,0,0,0.3)",
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(59,130,246,0.5)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = "0 4px 24px rgba(59,130,246,0.12)";
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(59,130,246,0.2)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = "0 2px 16px rgba(0,0,0,0.3)";
      }}
      onClick={openFlyout}
    >
      {/* Status bar mirrors intelligence card */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "10px 16px",
        borderBottom: "1px solid rgba(255,255,255,0.05)",
        background: "rgba(59,130,246,0.07)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{
            display: "inline-block", width: "7px", height: "7px", borderRadius: "50%",
            background: "#3b82f6", boxShadow: "0 0 6px rgba(59,130,246,0.7)", flexShrink: 0,
          }} />
          <span style={{ fontSize: "0.65rem", fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", color: "#60a5fa" }}>
            {ad.sponsor?.tagline || "Sponsored Content"}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "0.62rem", color: "#555", letterSpacing: "0.06em", textTransform: "uppercase" }}>Promoted</span>
          <button
            onClick={e => { e.stopPropagation(); setDismissed(true); }}
            style={{ background: "none", border: "none", cursor: "pointer", color: "#666", padding: "2px 4px", lineHeight: 1, fontSize: "1.1rem", display: "flex", alignItems: "center", transition: "color 0.15s" }}
            onMouseEnter={e => (e.currentTarget.style.color = "#fff")}
            onMouseLeave={e => (e.currentTarget.style.color = "#666")}
            aria-label="Dismiss ad"
          >×</button>
        </div>
      </div>

      {ad.sponsor?.image_url && (
        <div style={{ overflow: "hidden", height: "140px" }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={ad.sponsor.image_url} alt={ad.title} style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
        </div>
      )}

      <div style={{ padding: "16px 18px 18px" }}>
        <h3 style={{ margin: "0 0 8px", fontSize: "1rem", fontWeight: 700, lineHeight: 1.35, color: "#fff", letterSpacing: "-0.01em" }}>
          {ad.title}
        </h3>
        {ad.sponsor?.summary && (
          <p style={{
            margin: "0 0 14px", fontSize: "0.83rem", lineHeight: 1.6, color: "rgba(255,255,255,0.55)",
            display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden",
          }}>
            {ad.sponsor.summary}
          </p>
        )}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: "4px", fontSize: "0.8rem", fontWeight: 600, color: "#60a5fa", textShadow: "none" }}>
            {ad.sponsor?.cta_text || "Read More"}
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
            </svg>
          </span>
          <span style={{ fontSize: "0.72rem", color: "#444" }}>Sponsored Intelligence</span>
        </div>
      </div>
    </div>
  );
}

export default function GenericAd({ ad, onSponsorClick }: GenericAdProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hasViewed, setHasViewed] = useState(false);

  // Track View (Intersection Observer)
  useEffect(() => {
    if (!ad || hasViewed || !containerRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setHasViewed(true);
          // Ping backend to track view
          fetch(`/api/ads/render/${ad.id}`, { method: "POST" }).catch((err) =>
            console.error("Failed to track ad view", err)
          );
          observer.disconnect();
        }
      },
      { threshold: 0.5 } // Trigger when 50% visible
    );

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [ad, hasViewed]);

  const handleLinkClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const targetUrl = e.currentTarget.href;
    // Track click via ping or redirect, then go to URL
    // Actually, redirecting through the backend endpoint is better for reliable tracking:
    window.open(`/api/ads/click/${ad.id}`, "_blank", "noopener,noreferrer");
  };

  if (!ad) return null;

  // EXTERNAL NETWORK AD (e.g. AdSense)
  if (ad.ad_type === "external" && ad.external) {
    // We inject the script. React is tricky with raw <script> tags in dangerouslySetInnerHTML.
    // A safer approach for AdSense is often a dedicated component or useEffect, 
    // but for generic scripts we can try to parse and execute them.
    // Notice: dangerouslySetInnerHTML will NOT execute <script> tags natively in React mounting.
    
    // For a robust implementation, you might need a custom hook to extract and run the scripts,
    // but basic `iframe` or raw HTML works for some networks.
    return (
      <div
        ref={containerRef}
        className="ad-container ad-external"
        style={{
          width: "100%",
          margin: "0",
          borderRadius: "10px",
          overflow: "hidden",
          border: "1px solid rgba(255,255,255,0.06)",
          background: "rgba(255,255,255,0.025)"
        }}
      >
        {/* Header bar */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "6px 12px",
          borderBottom: "1px solid rgba(255,255,255,0.05)",
          background: "rgba(0,0,0,0.2)"
        }}>
          <span style={{ fontSize: "0.6rem", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "#555" }}>
            Advertisement
          </span>
          <span style={{ fontSize: "0.6rem", color: "#444" }}>
            {ad.external.network_name || "Sponsored"}
          </span>
        </div>
        {/* Ad script content */}
        <div
          style={{ width: "100%", minHeight: "90px", display: "flex", alignItems: "center", justifyContent: "center" }}
          dangerouslySetInnerHTML={{ __html: ad.external.script_code }}
        />
        <ScriptExecutor html={ad.external.script_code} containerRef={containerRef} />
      </div>
    );
  }

  // IMAGE BANNER AD
  if (ad.ad_type === "image" && ad.image) {
    return (
      <div 
        ref={containerRef}
        className="ad-container ad-image relative group overflow-hidden rounded-xl border border-border"
      >
        <span className="absolute top-2 right-2 z-10 text-[10px] font-bold uppercase tracking-wider text-white/70 bg-black/60 backdrop-blur px-2 py-1 rounded">
          Advertisement
        </span>
        <a 
          href={`/api/ads/click/${ad.id}`} 
          target="_blank" 
          rel="noopener noreferrer"
          className="block w-full h-full"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img 
            src={ad.image.image_url} 
            alt={ad.image.alt_text || ad.title}
            className="w-full object-cover transition-transform duration-500 group-hover:scale-[1.02]"
            style={{ maxHeight: "300px" }}
          />
        </a>
      </div>
    );
  }

  // SPONSORED CONTENT — styled like an intelligence card with a dismiss button
  // `dismissed` is component state so it resets on every page refresh
  if (ad.ad_type === "sponsor" && ad.sponsor) {
    return (
      <DismissableSponsored ad={ad} onSponsorClick={onSponsorClick} containerRef={containerRef} />
    );
  }

  return null;
}

// Helper to extract and run script tags from raw HTML string
function ScriptExecutor({ html, containerRef }: { html: string, containerRef: React.RefObject<HTMLDivElement | null> }) {
  useEffect(() => {
    if (!containerRef.current || !html) return;
    
    const scripts = containerRef.current.querySelectorAll("script");
    scripts.forEach(oldScript => {
      const newScript = document.createElement("script");
      Array.from(oldScript.attributes).forEach(attr => {
        newScript.setAttribute(attr.name, attr.value);
      });
      if (oldScript.innerHTML) {
        newScript.innerHTML = oldScript.innerHTML;
      }
      if (oldScript.parentNode) {
        oldScript.parentNode.replaceChild(newScript, oldScript);
      }
    });
  }, [html, containerRef]);

  return null;
}

