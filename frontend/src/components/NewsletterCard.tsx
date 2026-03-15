"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";

interface NewsletterCardProps {
  title: string;
  description: string;
}

export default function NewsletterCard({ title, description }: NewsletterCardProps) {
  const { user } = useAuth();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  // If already logged in/registered, we don't show the generic newsletter subscribe card
  if (user) return null;

  const handleSubscribe = async () => {
    if (!email.trim() || !email.includes("@")) return;
    setLoading(true);
    try {
      // For category pages, we "seamlessly ask for the full and register them"
      // We'll use the existing magic-register endpoint but specifically for newsletter context
      const res = await fetch("/api/auth/magic-register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, full_name: "Newsletter Subscriber" }),
      });
      if (res.ok) {
        setDone(true);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <div className="sidebar-card newsletter-card" style={{ textAlign: "center", padding: "32px 20px" }}>
        <div style={{ fontSize: "1.5rem", marginBottom: "8px" }}>✅</div>
        <div className="sidebar-title">Synthesizing...</div>
        <p className="newsletter-desc">Welcome to PAPERLY.. Your daily brief will arrive at 6 AM WAT.</p>
      </div>
    );
  }

  return (
    <div className="sidebar-card newsletter-card">
      <div className="sidebar-title">{title}</div>
      <p className="newsletter-desc">{description}</p>
      <div className="newsletter-form">
        <input
          type="email"
          className="newsletter-input"
          placeholder="Your email address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={loading}
        />
        <button className="newsletter-btn" onClick={handleSubscribe} disabled={loading}>
          {loading ? "..." : "Get Full Brief"}
        </button>
      </div>
    </div>
  );
}
