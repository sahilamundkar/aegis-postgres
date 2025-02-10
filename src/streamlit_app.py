# src/streamlit_app.py
import streamlit as st
from uuid import uuid4
from datetime import datetime

from src.config.config import get_settings
from src.services.database_service import DatabaseService
from src.services.embeddings_service import EmbeddingsService
from src.services.llm_service import LLMService
from src.utils.token_counter import TokenCounter
from src.utils.exceptions import TokenLimitError
from src.models.conversation import Message

class StreamlitApp:
    def __init__(self):
        st.set_page_config(page_title="Aegis", layout="wide")
        self.settings = get_settings()
        self.initialize_services()
        self.initialize_session_state()
        
    def initialize_services(self):
        """Initialize all required services"""
        try:
            self.db_service = DatabaseService()
            self.embeddings_service = EmbeddingsService()
            self.llm_service = LLMService()
            self.token_counter = TokenCounter()
            self.vectors = self.embeddings_service.load_or_create_embeddings()
        except Exception as e:
            st.error(f"Error initializing services: {str(e)}")
            st.stop()

    def initialize_session_state(self):
        """Initialize or get session state variables"""
        if "user_id" not in st.session_state:
            st.session_state.user_id = str(uuid4())
        if "conversation_id" not in st.session_state:
            st.session_state.conversation_id = None
            self.start_new_conversation()

    def start_new_conversation(self):
        """Start a new conversation"""
        try:
            conversation = self.db_service.create_conversation(
                user_id=st.session_state.user_id,
                metadata={"questions_asked": 0}
            )
            st.session_state.conversation_id = conversation.id
            
            # Add initial message
            initial_message = (
                "Hello! I'm Aegis, an AI Cybersecurity Auditor and an expert on "
                "ISO27001 and ISO27002 documentation. I can help you design a "
                "cybersecurity framework for your company. Please answer the questions "
                "that follow.\n\nQuestion 1: Can you describe your company's primary "
                "business activities and industries?"
            )
            self.db_service.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=initial_message,
                token_count=self.token_counter.count_tokens(initial_message)
            )
        except Exception as e:
            st.error(f"Error starting new conversation: {str(e)}")
            st.stop()

    def display_messages(self, conversation):
        """Display all messages in the conversation"""
        for message in conversation.messages:
            with st.chat_message(message.role):
                st.markdown(message.content)

    def handle_user_input(self, prompt: str, conversation):
        """Process user input and generate response"""
        try:
            # Check token limit
            if not self.token_counter.is_within_limit(prompt):
                raise TokenLimitError("Message exceeds token limit")

            # Add user message
            self.db_service.add_message(
                conversation_id=st.session_state.conversation_id,
                role="user",
                content=prompt,
                token_count=self.token_counter.count_tokens(prompt)
            )

            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate and add assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Ensure metadata exists and has questions_asked
                    if not hasattr(conversation, 'metadata'):
                        conversation.metadata = {}
                    if 'questions_asked' not in conversation.metadata:
                        conversation.metadata['questions_asked'] = 0

                    # Generate response
                    response = self.llm_service.generate_response(
                        message=prompt,
                        conversation=conversation,
                        vectors=self.vectors
                    )
                    st.markdown(response)

                    # Save assistant response
                    self.db_service.add_message(
                        conversation_id=st.session_state.conversation_id,
                        role="assistant",
                        content=response,
                        token_count=self.token_counter.count_tokens(response)
                    )

                    # Update questions_asked count if we're in the questioning phase
                    if conversation.metadata['questions_asked'] < 5:
                        conversation.metadata['questions_asked'] += 1
                        # Update the metadata in the database
                        self.db_service.update_conversation_metadata(
                            conversation_id=st.session_state.conversation_id,
                            metadata=conversation.metadata
                        )

        except TokenLimitError:
            st.error("Your message is too long. Please try a shorter message.")
        except Exception as e:
            st.error(f"Error processing message: {str(e)}")


    def render(self):
        """Main render method for the Streamlit app"""
        try:
            # Get current conversation
            conversation = self.db_service.get_conversation(st.session_state.conversation_id)
            if not conversation:
                self.start_new_conversation()
                conversation = self.db_service.get_conversation(st.session_state.conversation_id)

            # Display conversation
            self.display_messages(conversation)

            # Handle user input
            if prompt := st.chat_input("Your response here..."):
                self.handle_user_input(prompt, conversation)

            # Add sidebar options
            with st.sidebar:
                if st.button("Start New Conversation"):
                    self.start_new_conversation()
                    st.rerun()

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

def main():
    app = StreamlitApp()
    app.render()

if __name__ == "__main__":
    main()