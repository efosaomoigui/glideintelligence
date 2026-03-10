"""Quick import and field check script."""
import sys
sys.path.insert(0, '.')

try:
    from app.schemas.topic import TopicTrendingSchema
    fields = list(TopicTrendingSchema.model_fields.keys())
    required = ['category', 'overall_sentiment', 'sentiment_score', 'sentiment_breakdown', 'source_perspectives', 'regional_impacts']
    missing = [f for f in required if f not in fields]
    if missing:
        print(f"FAIL - Missing fields: {missing}")
        sys.exit(1)
    else:
        print(f"PASS - TopicTrendingSchema has all required fields")
        print(f"Fields: {fields}")
except Exception as e:
    print(f"FAIL - Import error: {e}")
    sys.exit(1)

try:
    from app.services.news_service import NewsService
    print("PASS - NewsService imports OK")
except Exception as e:
    print(f"FAIL - NewsService import error: {e}")
    sys.exit(1)

try:
    from app.jobs.generate_topic_analysis_job import GenerateTopicAnalysisJob
    print("PASS - GenerateTopicAnalysisJob imports OK")
except Exception as e:
    print(f"FAIL - GenerateTopicAnalysisJob import error: {e}")
    sys.exit(1)

print("All checks passed!")
