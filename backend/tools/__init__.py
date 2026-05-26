# tools/__init__.py
# Usage: from tools import TavilySearchTool

from .tavily_tool import TavilySearchTool, SearchResult, SearchResponse
from .grammar_tool import GrammarCheckTool, CrewAIGrammarCheckTool, GrammarMatch, GrammarCheckResponse
from .seo_tool import SEOKeywordAnalyzer, CrewAISEOTool, KeywordMetrics, SEOResponse
from .plagiarism_tool import PlagiarismDetector, CrewAIPlagiarismTool, PlagiarizedSentence, PlagiarismResponse