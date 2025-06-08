# Re-run required logic after kernel reset to generate the UML diagram again
import graphviz

# Create a UML class diagram using Graphviz
dot = graphviz.Digraph(format='png')
dot.attr(rankdir='LR', fontsize='10')

# Classes and properties
classes = {
    "Project": ["hasClient", "hasDesigner", "hasPurchasingAgent", "hasFurnitureItem", "hasDesignDocument", "hasBiddingDocument", "hasDeal", "hasSiteNature", "hasDesignStyle"],
    "Client": [],
    "Designer": [],
    "PurchasingAgent": [],
    "FurnitureItem": ["hasFunction", "isUsedInRoom", "hasProductID"],
    "DesignSpecifiedProduct": ["isFinalVersionOf"],
    "FinalInstalledProduct": ["wasIntendedAs"],
    "DesignDocument": ["submittedBy"],
    "BiddingDocument": ["handledBy"],
    "Deal": [],
    "ProjectSiteNature": [],
    "FunctionalUseClass": [],
    "RoomType": [],
    "TeamMember": [],
    "REAgent": [],
    "DesignStyle": [],
    "ImageAsset": ["taggedWith", "linkedToProject"],
    "AIModule": ["usesAIModel"],
    "DesignEffectImage": ["depictsProduct"],
    "RealPhoto": ["depictsProduct"]
}

# Add class nodes
for cls, props in classes.items():
    label = f"<<table border='0' cellborder='1' cellspacing='0'><tr><td bgcolor='lightblue'><b>{cls}</b></td></tr>"
    for prop in props:
        label += f"<tr><td align='left'>{prop}</td></tr>"
    label += "</table>>"
    dot.node(cls, label=label, shape='plaintext')

# Subclass relationships
dot.edge("DesignSpecifiedProduct", "FurnitureItem", arrowhead='empty', style='dashed', label="subclass")
dot.edge("FinalInstalledProduct", "FurnitureItem", arrowhead='empty', style='dashed', label="subclass")

# Object relationships
relationships = [
    ("Project", "Client", "hasClient"),
    ("Project", "Designer", "hasDesigner"),
    ("Project", "PurchasingAgent", "hasPurchasingAgent"),
    ("Project", "FurnitureItem", "hasFurnitureItem"),
    ("Project", "DesignDocument", "hasDesignDocument"),
    ("Project", "BiddingDocument", "hasBiddingDocument"),
    ("Project", "Deal", "hasDeal"),
    ("Project", "ProjectSiteNature", "hasSiteNature"),
    ("Project", "DesignStyle", "hasDesignStyle"),
    ("FurnitureItem", "FunctionalUseClass", "hasFunction"),
    ("FurnitureItem", "RoomType", "isUsedInRoom"),
    ("DesignDocument", "Designer", "submittedBy"),
    ("BiddingDocument", "TeamMember", "handledBy"),
    ("ImageAsset", "DesignStyle", "taggedWith"),
    ("ImageAsset", "Project", "linkedToProject"),
    ("AIModule", "REAgent", "usesAIModel"),
    ("FinalInstalledProduct", "DesignSpecifiedProduct", "wasIntendedAs"),
    ("DesignSpecifiedProduct", "FinalInstalledProduct", "isFinalVersionOf"),
    ("DesignEffectImage", "FurnitureItem", "depictsProduct"),
    ("RealPhoto", "FurnitureItem", "depictsProduct"),
]

# Add relationships as edges
for domain, range_, label in relationships:
    dot.edge(domain, range_, label=label)

# Render UML diagram
uml_output_path = "/mnt/data/skypad_uml_diagram"
dot.render(uml_output_path, cleanup=False)
uml_output_path + ".png"
