"use client";

import React from "react";
import Link from "next/link";

export default function SiteFooter() {
  const openInfo = (e: React.MouseEvent, topic: string) => {
    e.preventDefault();
    window.dispatchEvent(new CustomEvent("open-flyout", { 
      detail: { type: "info", infoType: topic } 
    }));
  };

  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div className="footer-top">
          <div className="footer-brand">
            <div className="logo">
              Gl<span className="accent">Intel</span>
            </div>
            <p className="footer-tagline">
              We don&apos;t publish news. We make sense of it. Glide-powered
              intelligence platform for Nigeria &amp; West Africa.
            </p>
          </div>

          <div>
            <div className="footer-col-title">Sectors</div>
            <div className="footer-links">
              <Link href="/economy">Economy</Link>
              <Link href="/politics">Politics</Link>
              <Link href="/business">Business</Link>
              <Link href="/security">Security</Link>
            </div>
          </div>

          <div>
            <div className="footer-col-title">Intelligence</div>
            <div className="footer-links">
              <Link href="/technology">Technology</Link>
              <Link href="/sport">Sport</Link>
              <Link href="/regional">Regional</Link>
              <Link href="/global-impact">Global Impact</Link>
            </div>
          </div>

          <div>
            <div className="footer-col-title">Company</div>
            <div className="footer-links">
              <a href="#" onClick={(e) => openInfo(e, "about")}>About Us</a>
              <a href="#" onClick={(e) => openInfo(e, "how-it-works")}>How It Works</a>
              <a href="#" onClick={(e) => openInfo(e, "transparency")}>Transparency</a>
              <a href="#" onClick={(e) => openInfo(e, "contact")}>Contact</a>
              <a href="#" onClick={(e) => openInfo(e, "newsletter")}>Newsletter</a>
            </div>
          </div>

          <div>
            <div className="footer-col-title">Legal</div>
            <div className="footer-links">
              <a href="#" onClick={(e) => openInfo(e, "privacy")}>Privacy Policy</a>
              <a href="#" onClick={(e) => openInfo(e, "terms")}>Terms of Service</a>
              <a href="#" onClick={(e) => openInfo(e, "editorial")}>Editorial Standards</a>
              <a href="#" onClick={(e) => openInfo(e, "sources")}>Source Policy</a>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <span>© 2026 Gl Intel News. All rights reserved.</span>
          <span>Powered by Scriptwall</span>
        </div>
      </div>
    </footer>
  );
}
