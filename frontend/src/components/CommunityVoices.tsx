"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

const VOICES = [
  {
    initials: "OA",
    color: "#c0392b",
    name: "Olumide Adegoke",
    role: "Financial Analyst",
    text: "The Naira rally is encouraging, but watch the oil price. If Brent drops below $75, this momentum evaporates overnight.",
  },
  {
    initials: "NK",
    color: "#27ae60",
    name: "Ngozi Kalu",
    role: "SME Owner",
    text: "VAT increase hits us twice: once on inputs, again on customer demand. SME tax relief doesn't offset this pain.",
  },
  {
    initials: "CM",
    color: "#2980b9",
    name: "Chidi Musa",
    role: "Political Analyst",
    text: "Revenue formula fight is really about 2027 elections. Follow the political math, not the economic rhetoric.",
  },
];

export default function CommunityVoices() {
  const [voices, setVoices] = useState<any[]>([]);
  const { user } = useAuth();

  useEffect(() => {
    fetch(`/api/sidebar`)
      .then(r => r.json())
      .then(data => {
         if (data.voices && data.voices.length > 0) {
            setVoices(data.voices.map((v: any) => ({
                initials: v.initials,
                color: v.color,
                name: v.name,
                role: v.role,
                text: v.quote
            })));
         }
      })
      .catch(e => console.error("Failed to load community voices", e));
  }, []);

  return (
    <div className="community-voices">
      <div className="voices-header">
        <div className="voices-title">Community Voices</div>
        {!user && (
          <button onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "login" } }))} style={{ fontSize: "0.8rem", color: "var(--accent)", background: "transparent", border: "none", cursor: "pointer" }}>
            Join Discussion →
          </button>
        )}
      </div>

      {voices.map((voice, i) => (
        <div key={i} className="voice-item">
          <div className="voice-header">
            <div className="voice-avatar" style={{ background: voice.color }}>
              {voice.initials}
            </div>
            <div className="voice-author">
              <div className="voice-name">{voice.name}</div>
              <div className="voice-role">{voice.role}</div>
            </div>
          </div>
          <p className="voice-text">
            &ldquo;
            {voice.text.split(/\s+/).length > 15 
              ? voice.text.split(/\s+/).slice(0, 15).join(" ") + "..." 
              : voice.text}
            &rdquo;
          </p>
        </div>
      ))}
    </div>
  );
}
