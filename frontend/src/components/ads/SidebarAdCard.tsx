"use client";

import React, { useEffect, useRef, useState } from "react";
import { AdData } from "./GenericAd";

/**
 * SidebarAdCard - A clean, unobtrusive ad card designed for the right-side panels
 * (Glide Pulse, Community Voices, Quick Poll section).
 * 
 * Supports:
 * - Sponsor ads: native card clickable to open the Sponsor flyout
 * - Image ads: image thumbnail with external click tracking
 * - External/script ads: a small contained slot for short AdSense banners
 */
export default function SidebarAdCard() {
  const [ad, setAd] = useState<AdData | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [viewed, setViewed] = useState(false);

  useEffect(() => {
    fetch("/api/ads/placement/sidebar_card")
      .then(r => {
        if (r.ok && r.headers.get("content-type")?.includes("application/json")) return r.json();
        return null;
      })
      .then(data => { if (data) setAd(data); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!ad || viewed || !containerRef.current) return;
    const observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        setViewed(true);
        fetch(`/api/ads/render/${ad.id}`, { method: "POST" }).catch(() => {});
        observer.disconnect();
      }
    }, { threshold: 0.5 });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [ad, viewed]);

  if (!ad) return null;

  // --- SPONSOR AD ---
  if (ad.ad_type === "sponsor" && ad.sponsor) {
    return (
      <div
        ref={containerRef}
        onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "sponsor", ...ad } }))}
        style={{
          marginTop: "20px",
          padding: "16px",
          background: "linear-gradient(135deg, rgba(59,130,246,0.07) 0%, rgba(139,92,246,0.07) 100%)",
          border: "1px solid rgba(59,130,246,0.25)",
          borderRadius: "12px",
          cursor: "pointer",
          transition: "border-color 0.2s",
        }}
        onMouseEnter={e => (e.currentTarget.style.borderColor = "rgba(59,130,246,0.55)")}
        onMouseLeave={e => (e.currentTarget.style.borderColor = "rgba(59,130,246,0.25)")}
      >
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
          <span style={{ fontSize: "0.7rem", fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", color: "#60a5fa" }}>
            {ad.sponsor.tagline || "Sponsored"}
          </span>
          <span style={{ fontSize: "0.7rem", color: "#555", letterSpacing: "0.05em", textTransform: "uppercase" }}>
            Promoted
          </span>
        </div>

        {/* Cover image */}
        {ad.sponsor.image_url && (
          <div style={{ marginBottom: "10px", borderRadius: "8px", overflow: "hidden", height: "80px" }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={ad.sponsor.image_url} alt={ad.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          </div>
        )}

        <div style={{ fontWeight: 600, fontSize: "1.05rem", color: "#fff", lineHeight: 1.4, marginBottom: "6px" }}>
          {ad.title}
        </div>
        <div style={{ fontSize: "0.95rem", color: "#aaa", lineHeight: 1.5, marginBottom: "10px" }}>
          {(ad.sponsor.summary || "").slice(0, 80)}{(ad.sponsor.summary?.length ?? 0) > 80 ? "…" : ""}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "0.95rem", fontWeight: 600, color: "#60a5fa" }}>
          {ad.sponsor.cta_text || "Learn More"}
          <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    );
  }

  // --- IMAGE AD ---
  if (ad.ad_type === "image" && ad.image) {
    return (
      <div ref={containerRef} style={{ marginTop: "20px" }}>
        <div style={{ fontSize: "0.6rem", color: "#555", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "6px" }}>
          Advertisement
        </div>
        <a
          href={`/api/ads/click/${ad.id}`}
          target="_blank"
          rel="noopener noreferrer"
          style={{ display: "block", borderRadius: "10px", overflow: "hidden", border: "1px solid rgba(255,255,255,0.06)" }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={ad.image.image_url}
            alt={ad.image.alt_text || ad.title}
            style={{ width: "100%", display: "block", maxHeight: "160px", objectFit: "cover" }}
          />
        </a>
      </div>
    );
  }

  // --- EXTERNAL / ADSENSE ---
  if (ad.ad_type === "external" && ad.external) {
    return (
      <div ref={containerRef} style={{ marginTop: "20px" }}>
        <div style={{ fontSize: "0.6rem", color: "#555", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "6px" }}>
          Advertisement
        </div>
        <div
          style={{ minHeight: "120px", background: "rgba(255,255,255,0.03)", border: "1px dashed rgba(255,255,255,0.1)", borderRadius: "10px", overflow: "hidden" }}
          dangerouslySetInnerHTML={{ __html: ad.external.script_code || "" }}
        />
      </div>
    );
  }

  return null;
}
