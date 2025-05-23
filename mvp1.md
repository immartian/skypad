# MVP1: "Bella" – The Skypad AI Chat Guide

## **Human+AI Strategy Blueprint (2025–2035)**

**Vision:** Combined with Human and Artificial Intelligence (HAI), empowering Skypad to become the world’s top intelligent, responsive, and visionary furniture partner for luxury hospitality, by integrating AI-driven intelligence across design, operations, and client engagement.

### **Core Objectives (What HAI Will Help Achieve)**

| Area | Goal |
| ----- | ----- |
| **Bidding Success** | Increase project bid success rate by 25–50% through smarter quoting, proposal optimization, and design personalization. |
| **Knowledge Sharing** | Centralize 24 years of project and vendor knowledge into a living system, enabling instant access, reuse, and innovation. |
| **Client Intelligence** | Predict client needs and preferences based on historical patterns and external market signals. |
| **Supply Chain Efficiency** | Optimize sourcing, vendor selection, and lead time management to reduce costs and delays by 15–30%. |
| **Operational Agility** | Detect risks and opportunities early in projects through real-time ERP/CRM monitoring and forecasting. |
| **Continuous Innovation** | Enable internal teams to explore new materials, sustainable practices, and design ideas through AI-scouted insights. |

### **Solution Framework (Architecture Overview)**

#### **1. Core Layer: Data Lakehouse**
- Aggregate ERP, CRM, VendorDB, and project files, including communications logs.
- Support structured and unstructured data.
- Enable future-proof analytics, ML, and BI.

#### **2. Intelligence Layer: Core Agent + Specialized Subagents**
- Vendor Intelligence Agent
- Client Insight Agent
- Design Optimizer Agent
- Operations and Timeline Agent
- Quoting & Proposal Agent
- Knowledge Graph for long-term memory

#### **3. System Integration Layer**
- Seamless connectors to live systems (low-risk, non-invasive).
- Event-driven architecture for near-real-time updates.

#### **4. Human-in-the-Loop Interfaces**
- Interactive Dashboards for conversations, ideas, approvals, insights, overrides.
- Natural language queries to Agent ("Bella").

### **Implementation Strategy (Agile + Recursive Development)**

| Phase | Focus | Deliverables |
| ----- | ----- | ----- |
| **Phase 0** | Baseline Assessment (1 month) | Map existing history documents (media), ERP, CRM, and Vendor systems; data quality audit. |
| **Phase 1** | Data Foundation (2-3 months) | Build the Lakehouse; basic ETL pipelines from ERP/CRM. |
| **Phase 2** | MVP Agents (2 months) | Deploy first Agent with 1–2 subagents (Vendor Intelligence + Client Insights). |
| **Phase 3** | Human-in-the-Loop (2 months) | Launch dashboards; gather user feedback loops. |
| **Phase 4** | Expansion (6-10 months) | Roll out Design and Operations agents; deepen Knowledge Graph. |
| **Phase 5** | Continuous Optimization (6-10 months) | Recursive learning: agents improve via feedback, retraining, better models quarterly. |

### **Key Principles**

- **Start Small, Scale Fast**: Prove value with minimum viable agents before scaling.
- **Human-AI Symbiosis**: AI augments, not replaces. Users are co-pilots.
- **Recursive Improvement**: Each release cycle gathers feedback, upgrades models, improves agent behavior.
- **Trust & Transparency**: Make AI decisions explainable to users to build confidence.
- **Business-Driven**: Every AI capability must tie back to clear business objectives (e.g., faster bids, better delivery).

### **Future Growth Pathways (Post-2030+)**

- Autonomous bidding agents that draft personalized proposals overnight.
- Digital twin of Skypad's supply chain for real-time optimization.
- AI copilots embedded in design software suggesting material innovations.
- Global client intelligence network that predicts hospitality design trends 12–18 months ahead.
- Skypad becomes not just a supplier—but a thought leader and innovation driver in luxury design.

## **Goal**
Deploy a simple, interactive chat agent (“Bella”) within the Skypad platform. Bella will act as a knowledgeable guide, summarizing the project’s vision, use cases, and architecture, and answering team questions to drive alignment and next-step planning.

---

## **Key Features**

1. **Chat Interface:**  
   - Add a chat panel to the Streamlit (or web) app.  
   - Users can ask Bella about Skypad’s AI strategy, use cases, and system vision.

2. **System Prompt/Core Knowledge:**  
   - Bella is initialized with a summary of the six use cases, the HAI strategy blueprint, and key architectural principles.  
   - She can explain the roadmap, clarify terminology (taxonomy, ontology, DAM, etc.), and provide context for ongoing discussions.

3. **Heuristic Guidance:**  
   - Bella can suggest next steps, highlight priorities (e.g., taxonomy before batch processing), and recommend best practices based on the blueprint.  
   - She can help facilitate team workshops or feedback sessions by answering “what’s next?” or “why are we doing this?” questions.

4. **Team Feedback Loop:**  
   - Use Bella’s chat logs to collect real team questions and pain points, informing future development and training.

---

## **Why This MVP?**

- **Accelerates team alignment** by making the vision and plan accessible to everyone, anytime.  
- **Reduces onboarding friction** for new team members or stakeholders.  
- **Lays the foundation** for Bella to become the “brain” of the platform, eventually connecting to data, analytics, and workflow automation.

---

## **Sample User Stories**

- “Bella, what are the main AI use cases for Skypad?”
- “How does the DAM fit into our roadmap?”
- “What’s the difference between taxonomy and ontology for our images?”
- “What’s the next step after MVP0?”
- “Summarize our HAI strategy in one paragraph.”

---

## **Technical Outline**

- **Chat Interface:** Integrate an LLM-based chat agent (OpenAI, Azure, or local) into the app.
- **System Prompt:** Includes:
  - The six use cases (from `use_cases.md`)
  - The HAI strategy and architecture blueprint (from `hai.md`)
  - Key principles and terminology
- **UI:** Simple chat interface with logging for future analysis.

---

## **Next Steps**

1. Define Bella’s system prompt using content from `use_cases.md` and `hai.md`.
2. Integrate a chat interface into the existing Streamlit app.
3. Test Bella’s responses with the team to refine her knowledge and guidance capabilities.
4. Use feedback to iterate and expand Bella’s functionality in future phases.
