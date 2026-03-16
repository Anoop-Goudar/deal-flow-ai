from services.conversation_service import ConversationService
from services.embedding_service import EmbeddingService
from services.eligibility_engine import EligibilityEngine
from services.llm_service import LLMService
from services.pipeline import PipelineService
from services.policy_service import PolicyService
from services.rag_service import RagService
from services.reply_suggestion_service import ReplySuggestionService
from services.task_router import TaskRouter


conversation_service = ConversationService()
embedding_service = EmbeddingService()
rag_service = RagService(embedding_service=embedding_service)
eligibility_engine = EligibilityEngine()
task_router = TaskRouter()
llm_service = LLMService()
reply_suggestion_service = ReplySuggestionService()
policy_service = PolicyService(rag_service=rag_service)
pipeline_service = PipelineService(
    conversation_service=conversation_service,
    rag_service=rag_service,
    eligibility_engine=eligibility_engine,
    task_router=task_router,
    llm_service=llm_service,
)
