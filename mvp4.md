# MVP4: Ontology Visualization & Conversational Context Integration

## Vision for MVP4

MVP4 extends RE-Skypad by introducing interactive ontology visualization and deep integration between chat content and the knowledge graph. Users can see, explore, and interact with the system’s ontology, while chat interactions dynamically highlight and update relevant nodes and relationships.

---

## Core Objectives

| Area                        | Goal                                                                                      |
|-----------------------------|------------------------------------------------------------------------------------------|
| **Ontology Visualization**  | Render the current Skypad ontology as an interactive, explorable graph.                  |
| **Chat-Graph Integration**  | Link chat content to ontology nodes/edges; focus/highlight relevant parts in real time.  |
| **Semantic Navigation**     | Allow users to navigate, search, and filter ontology visually and via chat.              |
| **Knowledge Enrichment**    | Enable chat to create, annotate, or link new nodes/edges in the ontology.                |
| **Contextual Awareness**    | Use ontology focus to inform Bella’s responses and memory.                               |

---

## Key Features

### 1. Ontology Visualization
- Interactive graph view of the current ontology (from `skypad_ontology_mvp.jsonld`)
- Node/edge types: Project, Designer, FurnitureItem, ImageAsset, etc.
- Visual cues for node types, relationships, and activity
- Zoom, pan, and search functionality

### 2. Chat-Driven Graph Focus
- When chat mentions an entity (e.g., "TheDorian", "Bedframe_123"), the graph focuses/highlights the relevant node(s)
- Bella can reference ontology nodes in responses
- Clicking a node can prompt Bella to explain or summarize it in chat

### 3. Semantic Navigation & Editing
- Users can search ontology from chat (e.g., "Show all GuestRoom items")
- Add or annotate nodes/edges via chat commands or UI
- Visual feedback for new or updated relationships

### 4. Knowledge Enrichment from Conversation
- Chat can create new nodes/edges (e.g., "Add a new Project: SkyLoft")
- Bella suggests ontology updates based on conversation context

### 5. Contextual Memory & Reasoning
- Bella’s memory and context window leverage ontology structure
- Visual indicators for which nodes are “in focus” or “recently discussed”
- Summarization and recommendations based on graph context

---

## Technical Architecture

- **Frontend:**  
  - React (web) with D3.js or Cytoscape.js for graph visualization  
  - Real-time chat-graph sync  
  - UI for node/edge creation and annotation

- **Backend:**  
  - FastAPI endpoints for ontology CRUD and search  
  - WebSocket for real-time updates  
  - GraphLite/JSON-LD as ontology store

- **Integration:**  
  - NLP entity recognition to map chat content to ontology nodes  
  - Event system to sync chat and graph focus

---

## User Stories

- "As a user, I want to see a live map of all projects, designers, and assets in the system."
- "When I mention 'TheDorian' in chat, the graph should highlight that project."
- "I want to add a new furniture item to the ontology directly from chat."
- "I want Bella to explain the relationship between two nodes I select."
- "I want to see which ontology nodes are most relevant to the current conversation."

---

## Success Metrics

- 80%+ of chat sessions trigger ontology focus events
- 50%+ of users interact with the ontology visualization
- <2s latency for chat-graph sync and updates
- 30%+ of new ontology nodes/edges created via chat

---

## Future Considerations

- Collaborative ontology editing
- Visual diff/history of ontology changes
- Deeper AI reasoning using graph structure

---
