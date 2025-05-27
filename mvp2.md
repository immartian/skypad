\
# MVP2: "RE-Skypad" – The Intelligent Core Agent & FastAPI/React Platform

## **Vision for MVP2**
Transition Skypad's AI platform to a robust, scalable architecture with a FastAPI backend and a React frontend. "Bella" (RE-Skypad) evolves into a central intelligent agent, capable of advanced knowledge retrieval, LLM interaction, and orchestrating backend services for tasks like image processing.

### **Core Objectives for MVP2**

| Area                      | Goal                                                                                                |
| ------------------------- | --------------------------------------------------------------------------------------------------- |
| **Architecture Migration**  | Rebuild the platform with FastAPI for the backend and React for the frontend.                       |
| **Intelligent Agent Core**  | Enhance "Bella" to interact with a Neo4j knowledge graph and manage embedding-based information.    |
| **Modular Task Services** | Develop backend services for image processing, supporting both on-demand and batch operations.        |
| **User Experience**       | Provide a modern, responsive UI/UX through the React frontend for chat and task management.         |
| **Scalability & Ops**     | Ensure the new architecture is scalable, maintainable, and ready for cloud deployment.              |

---

## **Key Features for MVP2**

1.  **FastAPI Backend:**
    *   All existing functionalities (image analysis, Bella chat) migrated to FastAPI endpoints.
    *   Secure API endpoints with authentication and authorization.
    *   Asynchronous task handling for long-running processes (e.g., batch image analysis).

2.  **React Frontend:**
    *   A new user interface built with React.
    *   Components for:
        *   Chatting with "Bella" (RE-Skypad).
        *   Image upload and analysis requests.
        *   Displaying analysis results.
        *   Viewing task statuses (for batch processing).
    *   User authentication and profile management (basic).

3.  **"Bella" (RE-Skypad) Agent Enhancements:**
    *   **Knowledge Graph Integration:**
        *   Connect to a Neo4j database to retrieve and store structured knowledge.
        *   Enable Bella to answer questions by querying the graph (e.g., "What projects involved vendor X?").
    *   **Embedding-based Retrieval:**
        *   Utilize vector embeddings for semantic search over documents or other unstructured data.
        *   Allow Bella to find relevant information from a corpus of Skypad documents.
    *   **Enhanced LLM Interaction:**
        *   Continue to use OpenAI (or other LLMs) for conversational AI and content generation.
        *   Potentially fine-tune or use more advanced prompting techniques based on retrieved context from Neo4j or embeddings.
    *   **Thought Process & Explainability:**
        *   Develop mechanisms for Bella to share "her" thought process or the sources of her information (e.g., "I found this in the project documents from 2023 related to X client").

4.  **Image Processing Task Services:**
    *   Backend services (potentially separate microservices or FastAPI background tasks) for:
        *   OpenAI Vision API analysis.
        *   Google Vision API analysis.
        *   Local CLIP model analysis.
    *   **On-demand processing:** Users can upload an image and get immediate results.
    *   **Batch processing:**
        *   Ability to submit a list of images (or a folder/bucket location) for analysis.
        *   A task queue system (e.g., Celery with Redis/RabbitMQ) to manage batch jobs.
        *   Users can view the status and results of batch tasks.

5.  **Database Integration:**
    *   **Primary Database (e.g., PostgreSQL):** For storing user data, task metadata, application state.
    *   **Neo4j:** For the knowledge graph.
    *   **Vector Database (e.g., Pinecone, Weaviate, or local Faiss/Chroma):** For storing and querying embeddings.

---

## **Architecture Overview for MVP2**

*   **Frontend:** React single-page application (SPA).
*   **Backend:** FastAPI application serving RESTful APIs.
    *   Authentication (e.g., JWT).
    *   Business logic for agent interactions, task management.
    *   Connectors to databases (PostgreSQL, Neo4j, Vector DB).
    *   Integration with LLM APIs.
*   **Task Processing:** Asynchronous workers (e.g., Celery) for image analysis and other long-running tasks.
*   **Datastores:**
    *   Relational DB (User accounts, application data, task queues).
    *   Graph DB (Neo4j for knowledge representation).
    *   Vector DB (Embeddings for semantic search).
*   **Deployment:** Containerized (Docker) and designed for cloud deployment (e.g., Kubernetes, Cloud Run).

---

## **Why This MVP?**

*   **Scalable Foundation:** Moves from a demo-centric Streamlit app to a production-ready architecture.
*   **Enhanced Intelligence:** Significantly boosts Bella's capabilities by integrating with knowledge graphs and semantic search.
*   **Improved User Experience:** Offers a dedicated, modern frontend for better interaction.
*   **Modular Design:** Separates concerns, making the system easier to develop, test, and maintain.
*   **Prepares for Advanced Use Cases:** Lays the groundwork for more complex AI agents and data integrations outlined in the long-term HAI strategy.

---

## **Sample User Stories for MVP2**

*   "As a user, I want to log in to the Skypad AI platform."
*   "As a user, I want to chat with Bella and ask her to retrieve information about past projects from the knowledge graph."
*   "As a user, I want Bella to find documents related to 'sustainable materials' using semantic search."
*   "As a user, I want to upload an image and select an analysis model (OpenAI, Google, CLIP) via the React interface."
*   "As a user, I want to submit a batch of 100 images for CLIP analysis and monitor the progress."
*   "As an admin, I want to see the logs of Bella's interactions and the tasks processed."

---

## **Technical Outline & Key Technologies**

*   **Frontend:** React, TypeScript (recommended), State Management (e.g., Redux, Zustand), UI Library (e.g., Material-UI, Ant Design).
*   **Backend:** Python, FastAPI, Pydantic.
*   **Databases:**
    *   PostgreSQL (or similar SQL DB).
    *   Neo4j.
    *   Vector Database (e.g., Weaviate, Pinecone, Faiss).
*   **Task Queue:** Celery, RabbitMQ/Redis.
*   **LLM:** OpenAI API.
*   **Deployment:** Docker, Uvicorn/Gunicorn.
*   **Authentication:** JWT or OAuth2.

---

## **Next Steps (High-Level for MVP2 Planning)**

1.  **Detailed Design:**
    *   API design for FastAPI.
    *   Database schemas (SQL, Graph, Vector).
    *   Frontend component breakdown and wireframes.
2.  **Setup Core Infrastructure:**
    *   FastAPI project structure.
    *   React project structure.
    *   Initial database setups (local or cloud).
3.  **Develop Authentication & User Management.**
4.  **Migrate/Re-implement Bella's Core Chat Logic in FastAPI.**
5.  **Integrate Neo4j and develop initial graph querying capabilities for Bella.**
6.  **Implement Embedding Generation and Vector Search for document retrieval.**
7.  **Develop Image Processing Task Services with a task queue.**
8.  **Build React Frontend components for chat, image analysis, and task monitoring.**
9.  **Testing (Unit, Integration, E2E).**
10. **Documentation.**
