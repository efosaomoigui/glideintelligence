"use client";

import React, { useEffect, useRef, useState } from "react";
import { AdData } from "./GenericAd";

/**
 * SidebarAdCard - A clean, unobtrusive ad card designed for the right-side panels
 * Supports Sponsor, Image, and External tags, with a uniform closable container.
 */
export default function SidebarAdCard({ 
  placement = "sidebar_card",
  fallbackPlacement
}: { 
  placement?: string;
  fallbackPlacement?: string;
}) {
  const [ad, setAd] = useState<AdData | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [viewed, setViewed] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const fetchAd = async (p: string) => {
      try {
        const r = await fetch(`/api/ads/placement/${p}`);
        if (r.ok && r.headers.get("content-type")?.includes("application/json")) {
          const data = await r.json();
          if (data && data.id) {
            setAd(data);
            return true;
          }
        }
      } catch (e) {
        console.error("Ad fetch failed", e);
      }
      return false;
    };

    const loadAds = async () => {
      const success = await fetchAd(placement);
      if (!success && fallbackPlacement) {
        await fetchAd(fallbackPlacement);
      }
    };

    loadAds();
  }, [placement, fallbackPlacement]);

  useEffect(() => {
    if (!ad || viewed || !containerRef.current || dismissed) return;
    const observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        setViewed(true);
        fetch(`/api/ads/render/${ad.id}`, { method: "POST" }).catch(() => {});
        observer.disconnect();
      }
    }, { threshold: 0.5 });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [ad, viewed, dismissed]);

  // Execute external scripts safely
  useEffect(() => {
    if (ad?.ad_type === "external" && ad.external?.script_code && containerRef.current && !dismissed) {
      const scripts = containerRef.current.querySelectorAll("script");
      scripts.forEach(oldScript => {
        const newScript = document.createElement("script");
        Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
        if (oldScript.innerHTML) newScript.innerHTML = oldScript.innerHTML;
        if (oldScript.parentNode) oldScript.parentNode.replaceChild(newScript, oldScript);
      });
    }
  }, [ad, dismissed]);

  if (!ad || dismissed) return null;

  const handleDismiss = (e: React.MouseEvent) => {
    e.stopPropagation();
    setDismissed(true);
  };

  const adTypeHeader = ad.ad_type === "sponsor" ? (ad.sponsor?.tagline || "Sponsored Content") :
                       ad.ad_type === "external" ? (ad.external?.network_name || "Advertisement") :
                       "Advertisement";

  return (
    <div
      ref={containerRef}
      style={{
        margin: "20px 0",
        position: "relative",
        borderRadius: "12px",
        background: "rgba(15,17,24,0.85)",
        border: "1px solid rgba(59,130,246,0.2)",
        backdropFilter: "blur(6px)",
        overflow: "hidden",
        transition: "border-color 0.2s, box-shadow 0.2s",
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
    >
      {/* Header Bar */}
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
            {adTypeHeader}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "0.62rem", color: "#555", letterSpacing: "0.06em", textTransform: "uppercase" }}>Promoted</span>
          <button
            onClick={handleDismiss}
            style={{ background: "none", border: "none", cursor: "pointer", color: "#666", padding: "2px 4px", lineHeight: 1, fontSize: "1.1rem", display: "flex", alignItems: "center", transition: "color 0.15s" }}
            onMouseEnter={e => (e.currentTarget.style.color = "#fff")}
            onMouseLeave={e => (e.currentTarget.style.color = "#666")}
            aria-label="Dismiss ad"
          >×</button>
        </div>
      </div>

      {/* Body Content */}
      <div style={{ padding: ad.ad_type === "external" ? "16px" : "0" }}>
        
        {/* SPONSOR */}
        {ad.ad_type === "sponsor" && ad.sponsor && (
           <div 
             onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "sponsor", ...ad } }))}
             style={{ cursor: "pointer" }}
           >
            {ad.sponsor.image_url && (
              <div style={{ overflow: "hidden", height: "140px" }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={ad.sponsor.image_url} alt={ad.title} style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
              </div>
            )}
            <div style={{ padding: "16px 18px 18px" }}>
              <h3 style={{ margin: "0 0 8px", fontSize: "1rem", fontWeight: 700, lineHeight: 1.35, color: "#fff", letterSpacing: "-0.01em" }}>
                {ad.title}
              </h3>
              {ad.sponsor.summary && (
                <p style={{
                  margin: "0 0 14px", fontSize: "0.83rem", lineHeight: 1.6, color: "rgba(255,255,255,0.55)",
                  display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden",
                }}>
                  {ad.sponsor.summary}
                </p>
              )}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: "4px", fontSize: "0.8rem", fontWeight: 600, color: "#60a5fa" }}>
                  {ad.sponsor.cta_text || "Learn More"}
                  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                  </svg>
                </span>
              </div>
            </div>
           </div>
        )}

        {/* IMAGE */}
        {ad.ad_type === "image" && ad.image && (
          <a
            href={`/api/ads/click/${ad.id}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ display: "block" }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={ad.image.image_url}
              alt={ad.image.alt_text || ad.title}
              style={{ width: "100%", display: "block", maxHeight: "250px", objectFit: "cover" }}
            />
          </a>
        )}

        {/* EXTERNAL (ADSENSE) */}
        {ad.ad_type === "external" && ad.external && (
          <div
            style={{ 
              minHeight: "120px", 
              background: "rgba(255,255,255,0.03)", 
              border: "1px dashed rgba(255,255,255,0.1)", 
              borderRadius: "8px", 
              overflow: "hidden",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#aaa",
              fontSize: "0.8rem"
            }}
            dangerouslySetInnerHTML={{ __html: ad.external.script_code || "Ad Slot" }}
          />
        )}
      </div>
    </div>
  );
}
