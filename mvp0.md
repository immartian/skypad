# MVP0: Streamlit Demo for Image Tagging and Explanation

## **Context**
* **Image tagging and organization** (Use Case 2) is one of the most tangible and high-impact items in Paul’s plan.
* It ties directly to business outcomes like faster marketing turnaround, searchable archives, and AI-enhanced presentations.
* It demonstrates your **initiative**, **technical capability**, and **product thinking**—all at once.

---

## MVP Definition

Build a simple, interactive web app using Streamlit that allows users to upload images and receive automatic tags, categories, and explanations using different vision models (OpenAI, Google Vision, or others).

### Features
1. Upload a batch of sample images (e.g., room scenes, furniture).
2. Select which model to use for tagging (OpenAI CLIP/GPT-4o, Google Vision, or a custom/other model).
3. For each image, display:
   - Detected categories/tags (e.g., “chair”, “public area”, “progress photo”)
   - Confidence scores (if available)
   - Short explanation or caption (if supported by the model)
   - Option to revise/approve tags
4. Optional: Search or group images by tag within the app.

### Tech Stack
- Python, Streamlit, APIs for OpenAI and Google Vision (with pluggable support for other models).

### Purpose
- Demonstrate rapid prototyping and technical initiative.
- Provide a visual, hands-on artifact for stakeholders.
- Start the conversation about architecture, model choice, and integration with future systems (e.g., DAM).

### Next Steps
- As the system matures, consider training a custom model on Skypad-specific data and integrating with internal asset management platforms.

---

## Why a Spike Demo Works Well Now

1. **Low-Risk, High Signal**: A small working prototype or even just a UI walkthrough shows immediate value with minimal resource ask.
2. **Focuses the Vision**: It turns the abstract blueprint into something visual and concrete—something Paul and his partner can rally behind.
3. **Starts the Architecture Conversation**: A spike can naturally lead to discussions about image pipelines, model training, DAM integration, and feedback loops.
4. **Positions You as the System Thinker**: You're not just executing use cases—you’re thinking of scalable, integrable systems.

---

## Model Choice Rationale

OpenAI's image models (like CLIP and GPT-4o’s vision capabilities) **can be a strong choice for the tagging stage**—especially in the early phases of a project where you want:

- **Fast, general-purpose image understanding**
- **Zero or minimal training**
- **Flexible tagging and explanation capabilities**

### Why It’s a Good Choice at the Image Processing Stage

| Need                                                         | OpenAI Model Capability                                            |
| ------------------------------------------------------------ | ------------------------------------------------------------------ |
| **Object/category recognition**                              | CLIP-based embeddings + GPT-4o vision can describe content broadly |
| **Contextual tagging (e.g., “hotel lobby,” “modern chair”)** | GPT-4o excels at contextual reasoning                              |
| **Caption or summary generation**                            | GPT-4o vision can generate human-like tags or descriptions         |
| **Rapid prototyping without setup**                          | No need to fine-tune a custom model initially                      |

### Caveats

- **Not trained specifically on Skypad’s domain** — So it won’t detect "Model A Chair" or know your custom design SKUs.
- **Not optimal for high-volume batch processing** — As OpenAI’s APIs may not be the most cost-effective or performant for thousands of images.
- **Tags may lack structure** — GPT-generated tags might require post-processing to fit a consistent taxonomy.

### Best Approach

Use OpenAI image models for:

- **Initial image cleaning and smart culling**
- **Zero-shot tagging and visual description**
- **Prototype generation of tag clusters or captioning**

Then, as the system matures:

- Train a **custom model** (e.g., fine-tuned CLIP, ViT, or YOLO) on Skypad-specific image archives and taxonomies.
- Integrate into a **Digital Asset Management (DAM)** system or internal search platform.

---

Would you like a starter Streamlit app scaffold for this MVP?
