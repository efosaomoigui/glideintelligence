import React from "react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import "./topic.css";

// Mocking server-side data fetching directly in the component for simplicity of migration
// In a real app, you would likely fetch this by ID/Slug 
async function getTopicDetails(idStr: string) {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    // Try to fetch by ID or slug using the dedicated endpoint
    const endpoint = isNaN(Number(idStr)) ? `slug/${idStr}` : idStr;
    const res = await fetch(`${apiUrl}/api/topic/${endpoint}`, {
      cache: "no-store",
    });
    
    if (!res.ok) {
       console.error(`Failed to fetch topic details for ${idStr}:`, res.status);
       return null;
    }
    
    return await res.json();
  } catch (error) {
    console.warn("Backend not running or error fetching topic details:", error instanceof Error ? error.message : "Unknown error");
  }
  return null;
}

// Helper to format numbers like 2800 -> 2.8K
function formatViews(num: number): string {
  if (!num) return "0";
  if (num >= 1000000) return (num / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
  if (num >= 1000) return (num / 1000).toFixed(1).replace(/\.0$/, "") + "K";
  return num.toString();
}

export default async function TopicDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = await params;
  const topicId = resolvedParams.id;
  const topicData = await getTopicDetails(topicId);

  // If no topic data is found at all
  if (!topicData) {
    return <div className="p-20 text-center text-xl">Topic not found</div>;
  }

  const title = topicData.title;
  const analysis = topicData.analysis || {};
  
  // Intelligence fields from Agent
  const executiveSummary = analysis.executive_summary || topicData.description || "No analysis available.";
  const whatToKnow = analysis.what_you_need_to_know || [];
  const keyTakeaways = analysis.key_takeaways || [];
  const drivers = analysis.drivers_of_story || [];
  const strategicImplications = analysis.strategic_implications || [];
  const regionalImpactItems = analysis.regional_impact || [];
  const confidenceScore = analysis.confidence_score || topicData.confidence_score || 0;

  const category = topicData.category || "General";
  const views = formatViews(topicData.view_count || 0);
  const comments = topicData.comment_count || 0;
  
  // Format the date using date-fns
  const updatedAt = topicData.updated_at ? formatDistanceToNow(new Date(topicData.updated_at), { addSuffix: true }) : "Recently";
  
  const sourcesCount = topicData.source_count || topicData.article_count || 0;

  return (
    <>
      {/* ─── TICKER ─── */}
      <div className="ticker">
        <div className="ticker-label">LIVE UPDATES</div>
        <div className="ticker-track">
          <span>CBN holds rates at 26.75% amid inflation concerns</span>
          <span>Naira strengthens to ₦1,450/$1 on parallel market</span>
          <span>NNPC announces ₦2.1T investment in Port Harcourt refinery</span>
        </div>
      </div>

      {/* ─── HEADER ─── */}
      <header className="site-header">
        <div className="header-top">
          <div className="logo">
            Gl<span className="accent">Intel News</span>
          </div>

          <nav className="breadcrumb">
            <Link href="/">Home</Link>
            <span>/</span>
            <Link href={`/${category.toLowerCase()}`}>{category}</Link>
            <span>/</span>
            <span>{title.length > 30 ? title.substring(0, 30) + "..." : title}</span>
          </nav>

          <div className="header-actions">
            <button className="btn btn-ghost">Share</button>
            <button className="btn btn-primary">Subscribe</button>
          </div>
        </div>
      </header>

      {/* ─── TOPIC HEADER ─── */}
      <section className="topic-header-section">
        <div className="topic-header-container">
          <div className="topic-meta">
            <div className="topic-badge developing">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="12" r="10" />
              </svg>
              Developing Story
            </div>
            <div className="update-badge">
              <div className="live-dot"></div>
              Updated {updatedAt}
            </div>
          </div>

          <h1 className="topic-title">
            {title}
          </h1>

          <div className="topic-stats">
            <div className="stat">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
              </svg>
              {sourcesCount} sources synthesized
            </div>
            <div className="stat">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              {Math.round(confidenceScore * 100)}% Confidence
            </div>
            <div className="stat">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
              </svg>
              {views} views
            </div>
          </div>
        </div>
      </section>

      {/* ─── MAIN CONTENT ─── */}
      <main className="main-content">
        <div className="content-area">
          
          {/* PILLAR 2: AI DEEP DIVE */}
          <section className="intelligence-section">
            <div className="section-label">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
              AI Intelligence Agent
            </div>
            
            <div className="intelligence-content">
              <h3>Executive Summary</h3>
              <p className="executive-summary-text">
                {executiveSummary}
              </p>

              {whatToKnow.length > 0 && (
                <>
                  <h3>What You Need to Know</h3>
                  <ul className="knowledge-list">
                    {whatToKnow.map((item: string, i: number) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </>
              )}

              {keyTakeaways.length > 0 && (
                <div className="key-takeaway">
                  <div className="takeaway-label">Key Takeaways</div>
                  <ul className="takeaway-list">
                    {keyTakeaways.map((item: string, i: number) => (
                      <li key={i} className="takeaway-text">{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {drivers.length > 0 && (
                <>
                  <h3>What Is Driving The Story?</h3>
                  <ul className="drivers-list">
                    {drivers.map((item: string, i: number) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </>
              )}

              {strategicImplications.length > 0 && (
                <div className="strategic-section">
                  <h3>Strategic Implications</h3>
                  <ul className="implications-list">
                    {strategicImplications.map((item: string, i: number) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            {/* PILLAR 5: SENTIMENT & FRAMING FALLBACKS */}
            {(topicData.analysis?.sentiment_summary || topicData.analysis?.framing_overview) && (
              <section className="intelligence-section fade-in" style={{ marginTop: '2rem' }}>
                <div className="section-label">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                  </svg>
                  Sentiment & Framing Analysis
                </div>
                <div className="intelligence-content">
                  {topicData.analysis?.sentiment_summary && (
                    <div style={{ marginBottom: '1.5rem' }}>
                      <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: 'var(--accent)' }}>Overall Sentiment</h3>
                      <p>{topicData.analysis.sentiment_summary}</p>
                    </div>
                  )}
                  {topicData.analysis?.framing_overview && (
                    <div>
                      <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: 'var(--accent)' }}>Framing & Narratives</h3>
                      <p>{topicData.analysis.framing_overview}</p>
                    </div>
                  )}
                </div>
              </section>
            )}
            </div>
          </section>

          {/* PILLAR 3: PERSPECTIVE MAP */}
          <section className="perspective-deep">
            <div className="section-label">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
              </svg>
              Perspective Analysis
            </div>
            <h2 className="section-title">How Different Groups Frame This Story</h2>

            <div className="perspective-groups">
              
              {topicData.source_perspectives && topicData.source_perspectives.length > 0 ? topicData.source_perspectives.map((p: any, i: number) => {
                 let s = p.sentiment === "positive" ? "positive" : p.sentiment === "negative" ? "negative" : "neutral";
                 return (
                  <div key={i} className={`perspective-group ${s}`}>
                    <div className="group-header">
                      <div className="group-name">{p.frame_label}</div>
                      <div className={`sentiment-badge ${s}`}>{p.sentiment_percentage || p.sentiment}</div>
                    </div>
                    <div className="group-summary">
                      {p.key_narrative}
                    </div>
                    <div className="group-quote">
                      "Context analysis extracted from overarching sources regarding {p.frame_label} focuses."
                      <span className="quote-source">— {p.source_name}</span>
                    </div>
                  </div>
                 )
              }) : (
                <div className="perspective-group neutral">
                    <div className="group-header">
                      <div className="group-name">General Media Overview</div>
                      <div className={`sentiment-badge neutral`}>Neutral</div>
                    </div>
                    <div className="group-summary">
                      Aggregated perspective of the developing story from synthesized sources.
                    </div>
                    <div className="group-quote">
                      "Waiting for enough signal to generate distinctive framing groups."
                      <span className="quote-source">— Platform Analysis</span>
                    </div>
                  </div>
              )}
            </div>
          </section>

          {/* PILLAR 4: REGIONAL IMPACT */}
          <section className="impact-deep">
            <div className="section-label">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              Regional Impact Analysis
            </div>
            <h2 className="section-title">
              What This Means for Nigeria & West Africa
            </h2>

            <div className="impact-categories">
              {regionalImpactItems.length > 0 ? (
                regionalImpactItems.map((item: string, idx: number) => (
                  <div key={idx} className="impact-category">
                    <div className="impact-cat-header">
                      <div className="impact-icon">🌍</div>
                      <div className="impact-cat-title">Regional Development</div>
                    </div>
                    <div className="impact-details">
                      <div className="impact-item">
                        <div className="impact-item-value">
                          {item}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : topicData.regional_impacts && topicData.regional_impacts.length > 0 ? (
                topicData.regional_impacts.map((imp: any, idx: number) => (
                  <div key={idx} className="impact-category">
                    <div className="impact-cat-header">
                      <div className="impact-icon">{imp.icon || "🌍"}</div>
                      <div className="impact-cat-title">{imp.impact_category || imp.title}</div>
                    </div>
                    <div className="impact-details">
                      <div className="impact-item">
                        <div className="impact-item-label">{imp.title}</div>
                        <div className="impact-item-value">
                          {imp.context || imp.value}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="impact-category">
                  <div className="impact-cat-header">
                    <div className="impact-icon">📊</div>
                    <div className="impact-cat-title">General Impact</div>
                  </div>
                  <div className="impact-details">
                    <div className="impact-item">
                      <div className="impact-item-label">Overview</div>
                      <div className="impact-item-value">
                        Current coverage maintains standard tracking vectors until deep analysis algorithms finalize.
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* PILLAR 1: SOURCE ARTICLES */}
          <section className="sources-section">
            <div className="section-label">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
              </svg>
              Source Articles
            </div>
            <h2 className="section-title">What the Original Sources Say</h2>

            <div className="source-articles">
              {topicData.articles && topicData.articles.map((art: any, i: number) => {
                const colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"];
                const initials = art.source_name ? art.source_name.substring(0,2).toUpperCase() : "GN";
                const bg = colors[i % colors.length];
                
                return (
                  <a href={art.url || "#"} key={i} className="source-article" target="_blank" rel="noopener noreferrer">
                    <div className="source-logo" style={{ background: bg, color: "#fff" }}>
                      {initials}
                    </div>
                    <div className="source-content">
                      <div className="source-name">{art.source_name || "Unknown Source"}</div>
                      <div className="source-headline">
                        {art.title}
                      </div>
                      <div className="source-snippet">
                        {art.snippet || art.content?.substring(0, 150) + "..."}
                      </div>
                      <div className="source-time">Published {art.published_at ? formatDistanceToNow(new Date(art.published_at), { addSuffix: true }) : "recently"}</div>
                    </div>
                  </a>
                )
              })}
            </div>
          </section>

          {/* PILLAR 5: COMMUNITY CONVERSATION */}
          <section className="community-section">
            <div className="section-label">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z"></path>
              </svg>
              Community Discussion
            </div>
            <h2 className="section-title">{comments} Comments</h2>

            <div className="comment-form">
              <textarea placeholder="Share your perspective on this topic..."></textarea>
              <div className="comment-actions">
                <div className="char-count">0 / 280</div>
                <button className="btn btn-primary">Post Comment</button>
              </div>
            </div>

            <div className="comments-list">
              <div className="comment">
                <div className="comment-header">
                  <div className="comment-avatar">OA</div>
                  <div className="comment-meta">
                    <div>
                      <span className="comment-author">System Generated</span>
                      <span className="comment-role">Automated Brief</span>
                    </div>
                    <div className="comment-time">{updatedAt}</div>
                  </div>
                </div>
                <div className="comment-text">
                  Discussion thread initialized for: "{title}". Join the conversation and share your perspectives.
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* SIDEBAR */}
        <aside className="sidebar">
          {/* Poll */}
          <div className="sidebar-card poll-card">
            <div className="sidebar-title">Quick Poll</div>
            <div className="poll-question">
              Will this emerging trend maintain its momentum through Q2 2026?
            </div>
            <div className="poll-options">
              <div className="poll-option">
                <label>
                  <input type="radio" name="poll" />
                  Yes, it's sustainable
                </label>
              </div>
              <div className="poll-option">
                <label>
                  <input type="radio" name="poll" />
                  Temporary shift
                </label>
              </div>
            </div>
            <div className="poll-results">1,847 responses • 14 hours left</div>
          </div>

          {/* AI Insights */}
          <div className="sidebar-card insights-card">
            <div className="sidebar-title">
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
              Live Insights
            </div>

            <div className="insight-item">
              <div className="insight-label">Sentiment Tracker</div>
              <div className="insight-value">68% Positive</div>
              <div className="insight-text">Analysis vector stable</div>
            </div>

            <div className="insight-item">
              <div className="insight-label">Expert Consensus</div>
              <div className="insight-value">Cautiously Optimistic</div>
              <div className="insight-text">Awaiting market confirmation</div>
            </div>
          </div>

        </aside>
      </main>

      {/* ─── FOOTER ─── */}
      <footer className="site-footer">
        <div className="footer-inner">
          <div className="footer-top">
            <div className="footer-brand">
              <div className="logo">Gl<span className="accent">Intel</span></div>
              <p className="footer-tagline">
                We don't publish news. We make sense of it. AI-powered intelligence platform for Nigeria & West Africa.
              </p>
            </div>
            <div>
              <div className="footer-col-title">Sections</div>
              <div className="footer-links">
                <a href="#">All Topics</a>
                <a href="#">Economy</a>
                <a href="#">Business</a>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <span>© 2026 Gl Intel. All rights reserved.</span>
            <span>Built in Lagos, Nigeria 🇳🇬</span>
          </div>
        </div>
      </footer>
    </>
  );
}
