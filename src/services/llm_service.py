# src/services/llm_service.py
import backoff
from langchain_groq import ChatGroq
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from src.config.config import get_settings
from src.models.conversation import Conversation

class LLMService:
    def __init__(self):
        self.settings = get_settings()
        self.llm = self._create_llm()
        
    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    def _create_llm(self):
        """Initialize LLM with retry decorator"""
        return ChatGroq(
            groq_api_key=self.settings.GROQ_API_KEY,
            model_name=self.settings.MODEL_NAME
        )
    
    def _format_conversation_history(self, messages):
        """Format conversation history for the LLM prompt"""
        return "\n".join([
            f"User: {msg.content}" if msg.role == "user" else f"Assistant: {msg.content}"
            for msg in messages
        ])
    
    def get_prompt_template(self, questions_asked: int, conversation_history: str) -> ChatPromptTemplate:
        """Get appropriate prompt template based on conversation state"""
        if questions_asked < 5:
            return ChatPromptTemplate.from_messages([
                ("system", f"""
                You are an AI assistant acting as an auditor to help a cybersecurity implementation engineer design the cybersecurity framework for their company using the ISO 27001 and ISO27002 standards.
                You have asked {questions_asked+1} questions so far.

                Conversation history:
                {conversation_history}

                Ask the next most appropriate question to understand the company better. Do not repeat any previous questions.
                The questions should be concise, restricted to one line and should cover only one topic.
                Format your questions as:
                Question {questions_asked+1}: [Your question here]
                """),
                ("human", "Context: {context}\n\nUser Input: {input}")
            ])
        elif questions_asked == 5:
            return ChatPromptTemplate.from_messages([
                ("system", f"""
                You are an AI assistant acting as an auditor to help a cybersecurity implementation engineer design the cybersecurity framework for their company using the ISO 27001 and ISO27002 standards.

                Conversation history:
                {conversation_history}

                Based on the information provided, here are the key guidelines from ISO27001/ISO27002 for your company's cybersecurity framework:
                [Your comprehensive guidelines here, mention 10 most relevant guidelines] (While answering the guidelines, you should mention which parts/subsections/annex of which document(ISO27001 or ISO27002) you are referencing, be as descriptive as possible)
                Support your answer about each guideline by mentioning how you narrowed your search to that guideline using the information about the company (answers from the user).
                """),
                ("human", "Context: {context}\n\nUser Input: {input}")
            ])
        else:
            return ChatPromptTemplate.from_messages([
                ("system", f"""
                You are an AI assistant acting as an auditor to answer questions about ISO27001 and ISO27002 implementation.

                Conversation history:
                {conversation_history}

                The user's question is the last item in the conversation.
                Please answer the user's query based on the information provided in the conversation history, the context, and your knowledge of ISO27001 and ISO27002 standards. Be specific and provide references to the relevant sections of the standards when appropriate.
                """),
                ("human", "Context: {context}\n\nUser Query: {input}")
            ])

    def generate_response(self, message: str, conversation: Conversation, vectors) -> str:
        """Generate response using LLM and vector store"""
        try:
            # Format conversation history from database records
            conversation_history = self._format_conversation_history(conversation.messages)
            
            # Get appropriate prompt template with conversation history
            prompt_template = self.get_prompt_template(
                conversation.metadata.get("questions_asked", 0),
                conversation_history
            )
            
            document_chain = create_stuff_documents_chain(self.llm, prompt_template)
            retriever = vectors.as_retriever()
            retrieval_chain = create_retrieval_chain(retriever, document_chain)
            
            response = retrieval_chain.invoke({
                'input': message,
                'context': conversation_history  # Pass history as context as well
            })
            
            return response['answer']
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            raise