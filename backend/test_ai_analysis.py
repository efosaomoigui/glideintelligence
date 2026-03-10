"""
Test script to trigger AI analysis for a topic and verify the complete pipeline.
This script will:
1. Find or create a test topic
2. Trigger AI analysis job
3. Monitor job completion
4. Verify generated data
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
load_dotenv()

from app.database import AsyncSessionLocal
from app.models.topic import Topic
from app.models.article import RawArticle
from app.models.intelligence import CategoryConfig, SourcePerspective, IntelligenceCard
from app.models.impact import RegionalImpact, ImpactDetail
from app.workers.tasks import ai_analysis_job
from sqlalchemy import select
from datetime import datetime


async def find_or_create_test_topic():
    """Find an existing topic or create a test one."""
    async with AsyncSessionLocal() as db:
        # Try to find an existing topic with articles
        result = await db.execute(
            select(Topic)
            .where(Topic.category.isnot(None))
            .limit(1)
        )
        topic = result.scalar_one_or_none()
        
        if topic:
            print(f"[OK] Found existing topic: {topic.title} (ID: {topic.id})")
            print(f"  Category: {topic.category}")
            
            # Check if it has articles
            articles_result = await db.execute(
                select(RawArticle)
                .join(RawArticle.topic_associations)
                .where(RawArticle.topic_associations.any(topic_id=topic.id))
            )
            articles = articles_result.scalars().all()
            print(f"  Articles: {len(articles)}")
            
            return topic.id
        else:
            print("WARNING: No topics found in database")
            print("  Please create a topic first by running the clustering job")
            return None


async def verify_analysis_results(topic_id: int):
    """Verify that AI analysis generated all expected data."""
    async with AsyncSessionLocal() as db:
        print(f"\n{'='*60}")
        print(f"VERIFYING ANALYSIS RESULTS FOR TOPIC {topic_id}")
        print(f"{'='*60}\n")
        
        # Get topic
        topic = await db.get(Topic, topic_id)
        if not topic:
            print("[ERROR] Topic not found")
            return
        
        print(f"Topic: {topic.title}")
        print(f"Category: {topic.category}")
        print(f"Overall Sentiment: {topic.overall_sentiment}")
        print(f"Sentiment Score: {topic.sentiment_score}")
        
        # Check sentiment breakdown
        from app.models.topic import TopicSentimentBreakdown
        sentiment_result = await db.execute(
            select(TopicSentimentBreakdown)
            .where(TopicSentimentBreakdown.topic_id == topic_id)
        )
        sentiment_items = sentiment_result.scalars().all()
        
        print(f"\n[SENTIMENT] Breakdown: {len(sentiment_items)} items")
        if sentiment_items:
            for item in sentiment_items[:5]:  # Show first 5
                print(f"  • {item.dimension_type}: {item.dimension_value}")
                print(f"    Sentiment: {item.sentiment} ({item.sentiment_score:+.2f})")
                print(f"    {item.description[:60]}...")
        else:
            print("  WARNING: No sentiment breakdown generated")
        
        # Check source perspectives
        perspectives_result = await db.execute(
            select(SourcePerspective)
            .where(SourcePerspective.topic_id == topic_id)
        )
        perspectives = perspectives_result.scalars().all()
        
        print(f"\n[PERSPECTIVES] Source Perspectives: {len(perspectives)} items")
        if perspectives:
            for persp in perspectives[:3]:  # Show first 3
                print(f"  • {persp.source_name}: '{persp.frame_label}'")
                print(f"    Sentiment: {persp.sentiment} ({persp.sentiment_percentage})")
        else:
            print("  WARNING: No source perspectives generated")
        
        # Check regional impacts
        impacts_result = await db.execute(
            select(RegionalImpact)
            .where(RegionalImpact.topic_id == topic_id)
        )
        impacts = impacts_result.scalars().all()
        
        print(f"\n[IMPACTS] Regional Impacts: {len(impacts)} items")
        if impacts:
            for impact in impacts:
                print(f"  • {impact.summary}")
                # Get details
                details_result = await db.execute(
                    select(ImpactDetail)
                    .where(ImpactDetail.regional_impact_id == impact.id)
                )
                details = details_result.scalars().all()
                for detail in details[:2]:  # Show first 2 details
                    print(f"    - {detail.label}: {detail.value[:50]}...")
        else:
            print("  WARNING: No regional impacts generated")
        
        # Check intelligence card
        card_result = await db.execute(
            select(IntelligenceCard)
            .where(IntelligenceCard.topic_id == topic_id)
        )
        card = card_result.scalar_one_or_none()
        
        print(f"\n[CARD] Intelligence Card:")
        if card:
            print(f"  {card.icon} {card.title}")
            print(f"  {card.description}")
            print(f"  Trend: {card.trend_percentage} ({'UP' if card.is_positive else 'DOWN'})")
        else:
            print("  WARNING: No intelligence card generated")
        
        print(f"\n{'='*60}")
        
        # Summary
        has_all = (
            len(sentiment_items) > 0 and
            len(perspectives) > 0 and
            len(impacts) > 0 and
            card is not None
        )
        
        if has_all:
            print("SUCCESS: ALL ANALYSIS COMPONENTS GENERATED SUCCESSFULLY!")
        else:
            print("WARNING: SOME COMPONENTS MISSING - Check logs for errors")
        
        print(f"{'='*60}\n")


async def main():
    """Main test function."""
    print("\n" + "="*60)
    print("AI ANALYSIS PIPELINE TEST")
    print("="*60 + "\n")
    
    # Step 1: Find or create test topic
    print("Step 1: Finding test topic...")
    topic_id = await find_or_create_test_topic()
    
    if not topic_id:
        print("\n[ERROR] Cannot proceed without a topic")
        print("\nTo create a topic:")
        print("1. Add some RSS feeds in the admin UI")
        print("2. Run the RSS ingestion job")
        print("3. Run the clustering job")
        print("4. Then run this test script again")
        return
    
    # Step 2: Trigger AI analysis
    print(f"\nStep 2: Triggering AI analysis for topic {topic_id}...")
    print("This may take 30-60 seconds depending on AI provider...")
    print("Providers will be tried in order: Gemini -> OpenAI -> Claude -> Ollama (Llama3)")
    
    try:
        # Call the worker task's internal async function directly
        from app.workers.tasks import ai_analysis_job
        from app.services.ai.summarization_service import SummarizationService
        from app.services.ai.content_generator import AIContentGenerator
        from app.models import (
            Topic, TopicAnalysis, TopicSentimentBreakdown, TopicArticle, 
            RawArticle, AISummary
        )
        from app.models.intelligence import CategoryConfig, SourcePerspective, IntelligenceCard
        from app.models.impact import RegionalImpact, ImpactCategory, ImpactDetail
        from datetime import datetime
        
        async with AsyncSessionLocal() as db:
            # Inline the analysis logic from the worker
            from sqlalchemy import select
            
            # 1. Fetch topic and its articles
            t_query = select(Topic).where(Topic.id == topic_id)
            t_res = await db.execute(t_query)
            topic = t_res.scalar_one_or_none()
            
            if not topic:
                print(f"[ERROR] Topic {topic_id} not found")
                return
            
            from sqlalchemy.orm import selectinload
            query = select(RawArticle).join(TopicArticle).where(TopicArticle.topic_id == topic_id).options(selectinload(RawArticle.source))
            result = await db.execute(query)
            articles = result.scalars().all()
            
            if not articles:
                print(f"[ERROR] No articles found for topic {topic_id}")
                return
            
            print(f"[OK] Found topic: {topic.title}")
            print(f"  Category: {topic.category}")
            print(f"  Articles: {len(articles)}")
            
            contents = [a.content for a in articles if a.content]
            combined_text = "\n\n".join(contents[:5])
            
            # 2. Fetch category configuration
            category_config = None
            if topic.category:
                config_query = select(CategoryConfig).where(CategoryConfig.category == topic.category.lower())
                config_res = await db.execute(config_query)
                category_config = config_res.scalar_one_or_none()
                
                if category_config:
                    print(f"[OK] Using category config for: {topic.category}")
                else:
                    print(f"[WARNING] No category config found for: {topic.category}")
            
            # 3. Initialize AI services
            ai_svc = SummarizationService(db)
            content_gen = AIContentGenerator(db)
            
            # 4. Generate basic summary
            print("\n[STEP] Generating basic summary...")
            analysis_data = await ai_svc.generate_summary_pipeline(contents)
            print(f"[OK] Summary generated using: {analysis_data.get('provider', 'unknown')}")
            
            # 5. Save basic analysis
            existing_analysis = await db.execute(
                select(TopicAnalysis).where(TopicAnalysis.topic_id == topic_id)
            )
            analysis = existing_analysis.scalar_one_or_none()
            
            if analysis:
                analysis.summary = analysis_data["summary"]
                analysis.facts = analysis_data["facts"]
                analysis.regional_framing = analysis_data["regional_framing"]
            else:
                analysis = TopicAnalysis(
                    topic_id=topic_id,
                    summary=analysis_data["summary"],
                    facts=analysis_data["facts"],
                    regional_framing=analysis_data["regional_framing"]
                )
                db.add(analysis)
            
            # Historical record
            ai_summary = AISummary(
                topic_id=topic_id,
                summary_type="60_second",
                content=analysis_data["summary"],
                bullet_points=analysis_data.get("facts", []),
                model_used=analysis_data.get("provider", "Unknown"),
                quality_score=analysis_data.get("confidence_score", 0.0),
                is_current=True,
                generated_at=datetime.now()
            )
            db.add(ai_summary)
            
            # 6. Generate enhanced analysis if category config exists
            if category_config:
                print("\n[STEP] Generating enhanced category-specific analysis...")
                
                # A. Sentiment breakdown
                print("  - Generating sentiment breakdown...")
                sentiment_items = await content_gen.generate_sentiment_breakdown(
                    topic.title,
                    combined_text,
                    category_config
                )
                print(f"[OK] Generated {len(sentiment_items)} sentiment items")
                
                # Save sentiment breakdown
                for item in sentiment_items:
                    sentiment = TopicSentimentBreakdown(
                        topic_id=topic_id,
                        dimension_type=item.get("dimension_type", "unknown"),
                        dimension_value=item.get("dimension_value", "unknown"),
                        sentiment=item.get("sentiment", "neutral"),
                        sentiment_score=item.get("sentiment_score", 0.0),
                        percentage=item.get("percentage", 0.0),
                        icon=item.get("icon", "❓"),
                        description=item.get("description", "No description")
                    )
                    db.add(sentiment)
                
                # B. Source perspectives
                print("  - Generating source perspectives...")
                sources_data = [
                    {
                        "name": a.source.name if a.source else "Unknown",
                        "headline": a.title,
                        "type": a.source.type if a.source else "unknown"
                    }
                    for a in articles if a.source
                ]
                
                if sources_data:
                    perspectives = await content_gen.generate_source_perspectives(
                        topic.title,
                        sources_data
                    )
                    print(f"[OK] Generated {len(perspectives)} perspectives")
                    
                    for persp in perspectives:
                        perspective = SourcePerspective(
                            topic_id=topic_id,
                            source_name=persp["source_name"],
                            source_type=persp.get("source_type"),
                            frame_label=persp["frame_label"],
                            sentiment=persp["sentiment"],
                            sentiment_percentage=persp["sentiment_percentage"],
                            key_narrative=persp["key_narrative"]
                        )
                        db.add(perspective)
                
                # C. Regional impacts
                print("  - Generating regional impacts...")
                impacts = await content_gen.generate_regional_impacts(
                    topic.title,
                    combined_text,
                    category_config
                )
                print(f"[OK] Generated {len(impacts)} impacts")
                
                
                # Save impacts - one RegionalImpact row per impact item (new schema)
                for impact_data in impacts:
                    cat_key = impact_data.get("impact_category", "general")
                    
                    # Try to find or create ImpactCategory
                    cat_query = select(ImpactCategory).where(ImpactCategory.slug == cat_key)
                    cat_result = await db.execute(cat_query)
                    impact_category = cat_result.scalar_one_or_none()
                    
                    if not impact_category:
                        impact_category = ImpactCategory(
                            name=cat_key.replace("_", " ").title(),
                            slug=cat_key,
                            icon=impact_data.get("icon", "📊"),
                            display_order=0
                        )
                        db.add(impact_category)
                        await db.flush()
                    
                    regional_impact = RegionalImpact(
                        topic_id=topic_id,
                        impact_category_id=impact_category.id,
                        impact_category=cat_key,
                        icon=impact_data.get("icon"),
                        title=f"{impact_data.get('region', 'Region')} Impact",
                        value=impact_data.get("description", "No description"),
                        severity=impact_data.get("severity"),
                        context=impact_data.get("context"),
                        summary=impact_data.get("description"),
                        is_current=True
                    )
                    db.add(regional_impact)
                
                # D. Calculate overall sentiment
                if sentiment_items:
                    avg_score = sum(s["sentiment_score"] for s in sentiment_items) / len(sentiment_items)
                    if avg_score > 0.2:
                        overall_sentiment = "positive"
                    elif avg_score < -0.2:
                        overall_sentiment = "negative"
                    else:
                        overall_sentiment = "neutral"
                else:
                    overall_sentiment = "neutral"
                
                # E. Intelligence card
                print("  - Generating intelligence card...")
                card_data = await content_gen.generate_intelligence_card(
                    topic.title,
                    topic.category,
                    overall_sentiment,
                    combined_text
                )
                print(f"[OK] Generated intelligence card")
                
                # Upsert: delete existing card for this topic first
                existing_card_res = await db.execute(
                    select(IntelligenceCard).where(IntelligenceCard.topic_id == topic_id)
                )
                existing_card = existing_card_res.scalar_one_or_none()
                if existing_card:
                    await db.delete(existing_card)
                    await db.flush()
                
                card = IntelligenceCard(
                    topic_id=topic_id,
                    category=card_data["category"],
                    icon=card_data["icon"],
                    title=card_data["title"],
                    description=card_data["description"],
                    trend_percentage=card_data["trend_percentage"],
                    is_positive=card_data["is_positive"],
                    display_order=0
                )
                db.add(card)
            
            # 7. Update topic metadata
            topic.status = "stable"
            topic.last_verified_at = datetime.now()
            
            await db.commit()
            print("\n[OK] Job completed successfully!")
            
    except Exception as e:
        safe_err = str(e).encode('ascii', errors='replace').decode('ascii')
        print(f"\n[ERROR] Job failed: {safe_err}")
        import traceback
        traceback.print_exc()
        print("\nCheck that:")
        print("1. At least one AI provider is enabled in the database")
        print("2. API keys are configured correctly in .env")
        print("3. The topic has a valid category")
        print("4. Ollama service is running (for fallback)")
        return
    
    # Step 3: Verify results
    print("\nStep 3: Verifying analysis results...")
    await verify_analysis_results(topic_id)
    
    print("\nSUCCESS: Test complete!")
    print("\nNext steps:")
    print("1. Check the API endpoint: GET /api/topic/{topic_id}")
    print("2. Check intelligence cards: GET /api/intelligence/cards")
    print("3. Implement frontend components using the integration guide")


if __name__ == "__main__":
    asyncio.run(main())
