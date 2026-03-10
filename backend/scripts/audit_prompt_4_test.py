import asyncio
import sys
import os
import json
from sqlalchemy import text, select
from datetime import datetime

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import get_db
from app.jobs.generate_topic_analysis_job import GenerateTopicAnalysisJob
from app.models import Topic

async def run_e2e_test():
    print("Running Audit Prompt 4 E2E Test...")
    
    async for session in get_db():
        # MOCKING AI CONTENT GENERATOR
        from unittest.mock import AsyncMock
        from app.services.ai.content_generator import AIContentGenerator
        
        # Define mock responses
        mock_sentiment = [
            {"dimension_type": "sector", "dimension_value": "Energy", "sentiment": "positive", "sentiment_score": 0.8, "percentage": 50.0, "icon": "⚡", "description": "Energy sector booms"},
            {"dimension_type": "stakeholder", "dimension_value": "Investors", "sentiment": "neutral", "sentiment_score": 0.1, "percentage": 30.0, "icon": "👥", "description": "Investors wait and see"},
            {"dimension_type": "sector", "dimension_value": "Manufacturing", "sentiment": "positive", "sentiment_score": 0.6, "percentage": 20.0, "icon": "🏭", "description": "Costs reducing"}
        ]
        
        mock_perspectives = [
             {"source_name": "The Guardian NG", "source_type": "mainstream", "frame_label": "Economic Optimism", "sentiment": "positive", "sentiment_percentage": "+40%", "key_narrative": "Great for FX"},
             {"source_name": "BusinessDay NG", "source_type": "business", "frame_label": "Market Rally", "sentiment": "positive", "sentiment_percentage": "+35%", "key_narrative": "Stocks up"}
        ]
        
        mock_impacts = [
            {"impact_category": "economic_growth", "icon": "📈", "region": "National", "value": "$17bn saved", "severity": "high", "description": "FX savings"},
            {"impact_category": "energy_security", "icon": "🔋", "region": "National", "value": "100% supply", "severity": "critical", "description": "Energy independence"},
            {"impact_category": "inflation", "icon": "📉", "region": "National", "value": "Lower costs", "severity": "medium", "description": "Input costs drop"}
        ]
        
        mock_card = {
            "category": "economic",
            "icon": "🛢️",
            "title": "Dangote Refinery Live",
            "description": "Full operations begin, saving $17bn FX.",
            "trend_percentage": "+100%",
            "is_positive": True
        }

        # Apply mocks
        AIContentGenerator.generate_sentiment_breakdown = AsyncMock(return_value=mock_sentiment)
        AIContentGenerator.generate_source_perspectives = AsyncMock(return_value=mock_perspectives)
        AIContentGenerator.generate_regional_impacts = AsyncMock(return_value=mock_impacts)
        AIContentGenerator.generate_intelligence_card = AsyncMock(return_value=mock_card)
        
        print("Mocks applied to AIContentGenerator.")

        # MOCK SUMMARIZATION SERVICE
        from app.services.ai.summarization_service import SummarizationService
        mock_summary = {
            "content": "This is a mocked summary.",
            "bullet_points": ["Point 1", "Point 2"],
            "key_takeaway": "Takeaway"
        }
        SummarizationService.generate_summary = AsyncMock(return_value=mock_summary)
        print("Mocks applied to SummarizationService.")

        TEST_TOPIC_ID = None
        import uuid
        slug_val = f"audit-test-{uuid.uuid4()}"
        try:
            # Step 1: Create Test Topic (ORM)
            topic = Topic(
                title=f'AUDIT TEST: Dangote Refinery {uuid.uuid4()}',
                slug=slug_val,
                category='economic',
                overall_sentiment='pending',
                sentiment_score=0.0,
                source_count=3,
                is_trending=False,
                status='developing'
            )
            session.add(topic)
            await session.flush()
            TEST_TOPIC_ID = topic.id
            print(f"Created Test Topic ID: {TEST_TOPIC_ID}")

            # Step 2: Insert Test Sources (ORM)
            from app.models.source import Source, SourceType, SourceCategory
            
            source1 = await session.execute(select(Source).where(Source.name == 'The Guardian NG'))
            s1 = source1.scalar_one_or_none()
            if not s1:
                s1 = Source(
                    name='The Guardian NG', 
                    type=SourceType.WEBSITE, 
                    url='https://guardian.ng', 
                    domain='guardian.ng',
                    category=SourceCategory.GENERAL,
                    is_active=True
                )
                session.add(s1)
            
            source2 = await session.execute(select(Source).where(Source.name == 'BusinessDay NG'))
            s2 = source2.scalar_one_or_none()
            if not s2:
                s2 = Source(
                    name='BusinessDay NG', 
                    type=SourceType.WEBSITE, 
                    url='https://businessday.ng', 
                    domain='businessday.ng',
                    category=SourceCategory.GENERAL, # Fallback to GENERAL if BUSINESS not found, or matching enum
                    is_active=True
                )
                session.add(s2)
            
            await session.flush()
            
            source1_id = s1.id
            source2_id = s2.id

            # Insert Articles and Link to Topic (ORM)
            from app.models.article import RawArticle
            from app.models.topic import TopicArticle
            from datetime import datetime
            
            # Article 1
            a1 = RawArticle(
                source_id=source1_id,
                title="Dangote Refinery Commercial Ops",
                content="Dangote Refinery has commenced full commercial operations, processing 650,000 barrels per day. This is expected to end fuel imports and save Nigeria $17 billion annually in foreign exchange. The refinery will supply 100% of Nigeria domestic petroleum needs starting this quarter.",
                url=f"https://example.com/article-{uuid.uuid4()}",
                published_at=str(datetime.now()),
                external_id=f"ext-article-1-{uuid.uuid4()}",
                content_hash=f"hash1-{uuid.uuid4()}",
                description="Short description",
                author="Test Author",
                image_url="https://example.com/image.jpg",
                snippet="Snippet...",
                word_count=100
            )
            session.add(a1)
            await session.flush()
            
            ta1 = TopicArticle(topic_id=TEST_TOPIC_ID, article_id=a1.id, relevance_score=0.9)
            session.add(ta1)
            
            # Article 2
            a2 = RawArticle(
                source_id=source2_id,
                title="Markets React to Refinery",
                content="Markets react positively to Dangote Refinery news. Energy stocks up 12%. Manufacturers expecting input cost reduction of 30-40% as fuel prices stabilize. Investors cautious about timeline for full product rollout.",
                url=f"https://example.com/article-{uuid.uuid4()}",
                published_at=str(datetime.now()),
                external_id=f"ext-article-2-{uuid.uuid4()}",
                content_hash=f"hash2-{uuid.uuid4()}",
                description="Short description 2",
                author="Test Author 2",
                image_url="https://example.com/image2.jpg",
                snippet="Snippet 2...",
                word_count=50
            )
            session.add(a2)
            await session.flush()
            
            ta2 = TopicArticle(topic_id=TEST_TOPIC_ID, article_id=a2.id, relevance_score=0.85)
            session.add(ta2)
            
            await session.commit()
            print("Test Data Inserted.")

            # Step 3: Run Job Manually
            print("Executing GenerateTopicAnalysisJob...")
            # Create a NEW session for the job to avoid transaction state issues? 
            # The job uses its own session? No, we pass `session`.
            # GenerateTopicAnalysisJob commits internally.
            job = GenerateTopicAnalysisJob(session)
            await job.execute(topic_id=TEST_TOPIC_ID)
            
            # Step 4: Verify Results
            print("\nVerifying Results...")
            
            # Check Topic
            res = await session.execute(text(f"SELECT overall_sentiment, sentiment_score, status FROM topics WHERE id = {TEST_TOPIC_ID}"))
            topic_row = res.fetchone()
            print(f"Topic Status: {topic_row}")

            # Check Breakdown
            res = await session.execute(text(f"SELECT dimension_type, dimension_value FROM topic_sentiment_breakdown WHERE topic_id = {TEST_TOPIC_ID}"))
            breakdown_rows = res.fetchall()
            print(f"Sentiment Breakdown Rows: {len(breakdown_rows)}")
            
            # Check Perspectives
            res = await session.execute(text(f"SELECT source_name FROM source_perspectives WHERE topic_id = {TEST_TOPIC_ID}"))
            perspective_rows = res.fetchall()
            print(f"Source Perspectives Rows: {len(perspective_rows)}")

            # Check Impacts
            res = await session.execute(text(f"SELECT impact_category, value, severity FROM regional_impacts r JOIN impact_details d ON r.id = d.regional_impact_id WHERE topic_id = {TEST_TOPIC_ID}"))
            impact_rows = res.fetchall()
            print(f"Regional Impact Detail Rows: {len(impact_rows)}")
            for r in impact_rows:
                 print(f" - {r}")
            
            # Check Card
            res = await session.execute(text(f"SELECT category, title, trend_percentage FROM intelligence_cards WHERE topic_id = {TEST_TOPIC_ID}"))
            card_rows = res.fetchall()
            print(f"Intelligence Card Rows: {len(card_rows)}")
            
            if card_rows:
                print(card_rows[0])

        except Exception as e:
            await session.rollback()
            print(f"\nFAIL: Exception during test: {e}")
            import traceback
            traceback.print_exc()
            with open("error.log", "w") as f:
                f.write(str(e))
                f.write("\n")
                f.write(traceback.format_exc())
        finally:
            # Clean Up
            if TEST_TOPIC_ID:
                try:
                    print("\nCleaning up...")
                    # Ensure clean transaction for delete
                    await session.rollback() 
                    await session.execute(text(f"DELETE FROM topics WHERE id = {TEST_TOPIC_ID}"))
                    await session.commit()
                    print("Test Topic Deleted.")
                except Exception as e2:
                    print(f"Error during cleanup: {e2}")
        return

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_e2e_test())
