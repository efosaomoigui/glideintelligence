"""Diagnose the state of topic analysis in the database - corrected table names."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from dotenv import load_dotenv
import os

load_dotenv()

async def check():
    db_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost/glideintelligence')
    engine = create_async_engine(db_url)
    async with AsyncSession(engine) as s:
        # List all tables first
        tables = (await s.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        ))).fetchall()
        print('=== TABLES IN DB ===')
        for r in tables:
            print(f'  {r[0]}')

        # Topics
        total = (await s.execute(text('SELECT COUNT(*) FROM topics'))).scalar()
        statuses = (await s.execute(text(
            'SELECT status, COUNT(*) FROM topics GROUP BY status ORDER BY COUNT(*) DESC'
        ))).fetchall()

        # topic_analysis table (correct name from model)
        try:
            with_analysis = (await s.execute(text('SELECT COUNT(*) FROM topic_analysis'))).scalar()
            real_analysis = (await s.execute(text(
                "SELECT COUNT(*) FROM topic_analysis WHERE summary IS NOT NULL AND LENGTH(summary) > 50"
            ))).scalar()
            no_analysis_topics = (await s.execute(text(
                'SELECT COUNT(*) FROM topics t LEFT JOIN topic_analysis ta ON ta.topic_id = t.id WHERE ta.id IS NULL'
            ))).scalar()
        except Exception as e:
            print(f'topic_analysis table error: {e}')
            with_analysis, real_analysis, no_analysis_topics = 0, 0, total

        # ai_summaries table
        try:
            ai_summaries = (await s.execute(text('SELECT COUNT(*) FROM ai_summaries'))).scalar()
            real_ai_summaries = (await s.execute(text(
                "SELECT COUNT(*) FROM ai_summaries WHERE content IS NOT NULL AND LENGTH(content) > 50"
            ))).scalar()
        except Exception as e:
            print(f'ai_summaries table error: {e}')
            ai_summaries, real_ai_summaries = 0, 0

        # source perspectives and regional impacts
        try:
            src_persp = (await s.execute(text('SELECT COUNT(*) FROM topic_source_perspectives'))).scalar()
        except:
            try:
                src_persp = (await s.execute(text('SELECT COUNT(*) FROM source_perspectives'))).scalar()
            except:
                src_persp = 'N/A'

        try:
            reg_impacts = (await s.execute(text('SELECT COUNT(*) FROM topic_regional_impacts'))).scalar()
        except:
            try:
                reg_impacts = (await s.execute(text('SELECT COUNT(*) FROM regional_impacts'))).scalar()
            except:
                reg_impacts = 'N/A'

        # Sample topics WITHOUT analysis
        try:
            sample_without = (await s.execute(text(
                "SELECT t.id, t.title, t.status FROM topics t "
                "LEFT JOIN topic_analysis ta ON ta.topic_id = t.id "
                "WHERE ta.id IS NULL LIMIT 5"
            ))).fetchall()
        except:
            sample_without = []

        # Sample topics WITH analysis
        try:
            sample_with = (await s.execute(text(
                "SELECT t.id, t.title, t.status, LEFT(ta.summary, 100) as summary FROM topics t "
                "JOIN topic_analysis ta ON ta.topic_id = t.id "
                "WHERE LENGTH(ta.summary) > 50 LIMIT 3"
            ))).fetchall()
        except:
            sample_with = []

        print(f'\n=== ANALYSIS STATE ===')
        print(f'Total topics:                  {total}')
        print(f'Topics with topic_analysis:    {with_analysis}')
        print(f'  - real (>50 chars):          {real_analysis}')
        print(f'  - missing analysis:          {no_analysis_topics}')
        print(f'AI Summaries rows:             {ai_summaries}')
        print(f'  - real ai_summaries:         {real_ai_summaries}')
        print(f'Source perspectives rows:      {src_persp}')
        print(f'Regional impacts rows:         {reg_impacts}')
        print(f'\nTopic status breakdown:')
        for row in statuses:
            print(f'  {row[0]}: {row[1]}')
        if sample_with:
            print(f'\nSample WITH real analysis:')
            for r in sample_with:
                print(f'  ID={r[0]} [{r[2]}] {r[1][:50]}')
                print(f'    -> {r[3]}...')
        if sample_without:
            print(f'\nSample WITHOUT analysis:')
            for r in sample_without:
                print(f'  ID={r[0]} [{r[2]}] {r[1][:60]}')

asyncio.run(check())
