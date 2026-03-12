from app.models.base import Base
from app.models.region import TopicRegionalCategory
from app.models.source import Source, SourceHealth, SourceType
from app.models.article import RawArticle, ArticleEntity, ArticleEmbedding, YouTubeVideo, CollectionJob
from app.models.topic import Topic, TopicArticle, TopicAnalysis, TopicSentimentBreakdown, TopicTrend, TopicVideo, AISummary, SummaryUpdate
from app.models.user import User
from app.models.interaction import Comment, CommentVote, Poll, PollOption, PollVote, CommunityInsight
from app.models.perspective import SourceGroup, SourceGroupMember, TopicPerspective, PerspectiveQuote, SentimentAnalysis
from app.models.impact import ImpactCategory, RegionalImpact, ImpactDetail, ImpactMetric
from app.models.intelligence import CategoryConfig, SourcePerspective, IntelligenceCard
from app.models.common import Vertical, Tag, TopicTag, UserPreference, AnalyticsEvent
from app.models.audit import AuditLog
from app.models.job import Job
from app.models.settings import AIProvider, FeatureFlag, AIProviderType
from app.models.ai_usage import AIUsageLog
from app.models.ads import Ad, AdExternalNetwork, AdSponsor, AdImage, AdEvent

