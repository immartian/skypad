import React, { useEffect, useState, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { forceCollide } from 'd3-force';
import styles from './OntologyVisualization.module.css';

interface OntologyNode {
  id: string;
  name: string;
  type: string;
  color: string;
  size: number;
  focused?: boolean;
}

interface OntologyLink {
  source: string;
  target: string;
  relationship: string;
  color: string;
}

interface OntologyData {
  nodes: OntologyNode[];
  links: OntologyLink[];
}

interface OntologyVisualizationProps {
  focusedEntities?: string[];
  onNodeClick?: (node: OntologyNode) => void;
}

const OntologyVisualization: React.FC<OntologyVisualizationProps> = ({ 
  focusedEntities = [], 
  onNodeClick 
}) => {
  const [ontologyData, setOntologyData] = useState<OntologyData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const forceRef = useRef<any>(null);

  useEffect(() => {
    loadOntologyData();
  }, []);

  // Stabilize the force simulation
  useEffect(() => {
    if (forceRef.current && ontologyData.nodes.length > 0) {
      const fg = forceRef.current;
      // Set up more stable force parameters
      fg.d3Force('link')?.strength(0.2).distance(80);
      fg.d3Force('charge')?.strength(-400);
      fg.d3Force('center')?.strength(0.05);
      
      // Add collision force to prevent overlapping
      fg.d3Force('collision', forceCollide().radius((node: any) => {
        const nodeData = node as any;
        const rectWidth = nodeData.__bckgDimensions ? nodeData.__bckgDimensions[0] : 100;
        const rectHeight = nodeData.__bckgDimensions ? nodeData.__bckgDimensions[1] : 30;
        return Math.max(rectWidth, rectHeight) / 2 + 10;
      }).strength(0.8));
    }
  }, [ontologyData]);

  useEffect(() => {
    // Update node focus when focusedEntities changes
    if (ontologyData.nodes.length > 0) {
      ontologyData.nodes.forEach(node => {
        const shouldBeFocused = focusedEntities.includes(node.name) || focusedEntities.includes(node.id);
        node.focused = shouldBeFocused;
        node.size = shouldBeFocused ? 8 : 5;
      });
    }
  }, [focusedEntities, ontologyData.nodes]);

  const loadOntologyData = async () => {
    try {
      // For now, we'll load the static ontology file and transform it
      const response = await fetch('/lattice/skypad_ontology_mvp.jsonld');
      const jsonLdData = await response.json();
      
      const transformedData = transformJsonLdToGraph(jsonLdData);
      setOntologyData(transformedData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load ontology:', error);
      setLoading(false);
    }
  };

  const transformJsonLdToGraph = (jsonLdData: any[]): OntologyData => {
    const nodes: OntologyNode[] = [];
    const links: OntologyLink[] = [];
    const nodeMap = new Map();

    // Define color scheme for different node types
    const colorMap: { [key: string]: string } = {
      'Project': '#3B82F6',
      'Designer': '#10B981',
      'FurnitureItem': '#F59E0B',
      'Client': '#EF4444',
      'PurchasingAgent': '#8B5CF6',
      'TeamMember': '#6B7280',
      'ImageAsset': '#F97316',
      'RoomType': '#06B6D4',
      'DesignStyle': '#EC4899',
      'ProjectSiteNature': '#84CC16',
      'FunctionalUseClass': '#64748B',
      'BiddingDocument': '#14B8A6',
      'Deal': '#F472B6',
      'DesignDocument': '#A855F7',
      'AIModule': '#22D3EE',
      'REAgent': '#FB7185',
      'default': '#9CA3AF'
    };

    // Process entities to create nodes
    jsonLdData.forEach(item => {
      if (item['@id'] && item['@id'].includes('#') && !item['@id'].endsWith('ontology')) {
        const entityId = item['@id'];
        const entityName = entityId.split('#')[1];
        
        // Determine node type
        let nodeType = 'Unknown';
        if (item['@type']) {
          const types = Array.isArray(item['@type']) ? item['@type'] : [item['@type']];
          nodeType = types[0].split('#')[1] || types[0].split('/').pop() || 'Unknown';
        }

        // Skip OWL classes and properties for cleaner visualization
        if (nodeType === 'Class' || nodeType === 'ObjectProperty') return;

        nodes.push({
          id: entityId,
          name: entityName,
          type: nodeType,
          color: colorMap[nodeType] || colorMap.default,
          size: 5,
          focused: false
        });

        nodeMap.set(entityId, entityName);
      }
    });

    // Process relationships to create links
    jsonLdData.forEach(item => {
      if (item['@id'] && nodeMap.has(item['@id'])) {
        Object.keys(item).forEach(key => {
          if (key.startsWith('http://skypad.ai/ontology#')) {
            const relationship = key.split('#')[1];
            const values = Array.isArray(item[key]) ? item[key] : [item[key]];
            
            values.forEach((value: any) => {
              if (value && value['@id'] && nodeMap.has(value['@id'])) {
                links.push({
                  source: item['@id'],
                  target: value['@id'],
                  relationship,
                  color: '#9CA3AF'
                });
              }
            });
          }
        });
      }
    });

    return { nodes, links };
  };

  const handleNodeClick = (node: any) => {
    // Toggle focus state directly on the node object that's being used by the force graph
    node.focused = !node.focused;
    node.size = node.focused ? 8 : 5;
    
    // Also update our data structure for consistency
    const targetNode = ontologyData.nodes.find(n => n.id === node.id);
    if (targetNode) {
      targetNode.focused = node.focused;
      targetNode.size = node.size;
    }

    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading ontology...</div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3>Skypad Knowledge Graph</h3>
        <div className={styles.legend}>
          <span className={styles.legendItem}>
            <span className={styles.legendColor} style={{ backgroundColor: '#3B82F6' }}></span>
            Projects
          </span>
          <span className={styles.legendItem}>
            <span className={styles.legendColor} style={{ backgroundColor: '#10B981' }}></span>
            Designers
          </span>
          <span className={styles.legendItem}>
            <span className={styles.legendColor} style={{ backgroundColor: '#F59E0B' }}></span>
            Furniture
          </span>
          <span className={styles.legendItem}>
            <span className={styles.legendColor} style={{ backgroundColor: '#EF4444' }}></span>
            Clients
          </span>
        </div>
      </div>
      <div className={styles.graphContainer}>
        <ForceGraph2D
          ref={forceRef}
          graphData={ontologyData}
          nodeId="id"
          nodeCanvasObject={(node: any, ctx, _globalScale) => {
            // Draw rectangular node
            const label = node.name;
            const fontSize = node.focused ? 16 : 14;
            ctx.font = `${fontSize}px Sans-Serif`;
            const textWidth = ctx.measureText(label).width;
            const paddingX = 12;
            const paddingY = 8;
            const rectWidth = textWidth + paddingX * 2;
            const rectHeight = fontSize + paddingY * 2;
            
            // Draw node background
            ctx.fillStyle = node.focused ? '#FF6B6B' : node.color;
            ctx.strokeStyle = node.focused ? '#FB4949' : 'rgba(0,0,0,0.2)';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.roundRect(node.x - rectWidth / 2, node.y - rectHeight / 2, rectWidth, rectHeight, 5);
            ctx.fill();
            ctx.stroke();
            
            // Draw node text
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#FFFFFF';
            ctx.fillText(label, node.x, node.y);

            // Set node size for collision detection
            node.__bckgDimensions = [rectWidth, rectHeight];
            node.size = Math.max(rectWidth, rectHeight) / 2;
          }}
          nodePointerAreaPaint={(node: any, color, ctx) => {
            // Draw invisible hit area for interaction
            if (node.__bckgDimensions) {
              ctx.fillStyle = color;
              ctx.fillRect(
                node.x - node.__bckgDimensions[0] / 2,
                node.y - node.__bckgDimensions[1] / 2,
                node.__bckgDimensions[0],
                node.__bckgDimensions[1]
              );
            }
          }}
          linkCanvasObjectMode={() => 'after'}
          linkCanvasObject={(link: any, ctx) => {
            // Always use up-to-date node positions and rectangle sizes
            const sourceNode = typeof link.source === 'object' ? link.source : ontologyData.nodes.find(n => n.id === link.source);
            const targetNode = typeof link.target === 'object' ? link.target : ontologyData.nodes.find(n => n.id === link.target);
            if (!sourceNode || !targetNode || typeof sourceNode.x !== 'number' || typeof targetNode.x !== 'number') return;

            // Calculate dimensions based on current state (focused or not)
            const calculateNodeDimensions = (node: any) => {
              const label = node.name;
              const fontSize = node.focused ? 16 : 14;
              ctx.font = `${fontSize}px Sans-Serif`;
              const textWidth = ctx.measureText(label).width;
              const paddingX = 12;
              const paddingY = 8;
              const rectWidth = textWidth + paddingX * 2;
              const rectHeight = fontSize + paddingY * 2;
              return [rectWidth, rectHeight];
            };

            // Always recalculate dimensions to handle focus state changes
            const sourceDimensions = calculateNodeDimensions(sourceNode);
            const targetDimensions = calculateNodeDimensions(targetNode);
            
            // Helper to get intersection point of a line with a rectangle
            function rectEdgeIntersection(
              x: number, y: number, w: number, h: number,
              x1: number, y1: number, x2: number, y2: number
            ) {
              const dx = x2 - x1;
              const dy = y2 - y1;
              
              // If nodes are at the same position, return the center
              if (Math.abs(dx) < 0.001 && Math.abs(dy) < 0.001) {
                return { x, y };
              }
              
              let minT = Infinity;
              let ix = x, iy = y;
              const sides = [
                { x3: x - w / 2, y3: y - h / 2, x4: x - w / 2, y4: y + h / 2 }, // left
                { x3: x + w / 2, y3: y - h / 2, x4: x + w / 2, y4: y + h / 2 }, // right
                { x3: x - w / 2, y3: y - h / 2, x4: x + w / 2, y4: y - h / 2 }, // top
                { x3: x - w / 2, y3: y + h / 2, x4: x + w / 2, y4: y + h / 2 }, // bottom
              ];
              
              for (const { x3, y3, x4, y4 } of sides) {
                const denom = (dx) * (y4 - y3) - (dy) * (x4 - x3);
                if (Math.abs(denom) < 0.001) continue; // parallel lines
                
                const t = ((x1 - x3) * (y4 - y3) - (y1 - y3) * (x4 - x3)) / denom;
                const u = -((dx) * (y1 - y3) - (dy) * (x1 - x3)) / denom;
                
                if (t > 0 && u >= 0 && u <= 1 && t < minT) {
                  minT = t;
                  ix = x1 + t * dx;
                  iy = y1 + t * dy;
                }
              }
              return { x: ix, y: iy };
            }
            
            // Calculate intersection points correctly
            const s = rectEdgeIntersection(
              sourceNode.x,
              sourceNode.y,
              sourceDimensions[0],
              sourceDimensions[1],
              sourceNode.x,
              sourceNode.y,
              targetNode.x,
              targetNode.y
            );
            const t = rectEdgeIntersection(
              targetNode.x,
              targetNode.y,
              targetDimensions[0],
              targetDimensions[1],
              sourceNode.x,
              sourceNode.y,
              targetNode.x,
              targetNode.y
            );
            
            // Only draw if we have valid intersection points
            if (isFinite(s.x) && isFinite(s.y) && isFinite(t.x) && isFinite(t.y)) {
              ctx.beginPath();
              ctx.moveTo(s.x, s.y);
              ctx.lineTo(t.x, t.y);
              ctx.strokeStyle = link.color;
              ctx.lineWidth = 1.5;
              ctx.stroke();
              
              // Draw arrow at the end
              const arrowLength = 6;
              const arrowAngle = Math.atan2(t.y - s.y, t.x - s.x);
              if (isFinite(arrowAngle)) {
                ctx.beginPath();
                ctx.moveTo(t.x, t.y);
                ctx.lineTo(
                  t.x - arrowLength * Math.cos(arrowAngle - Math.PI / 6),
                  t.y - arrowLength * Math.sin(arrowAngle - Math.PI / 6)
                );
                ctx.lineTo(
                  t.x - arrowLength * Math.cos(arrowAngle + Math.PI / 6),
                  t.y - arrowLength * Math.sin(arrowAngle + Math.PI / 6)
                );
                ctx.closePath();
                ctx.fillStyle = link.color;
                ctx.fill();
              }
              
              // Draw relationship label in the middle
              if (link.relationship) {
                const textX = s.x + (t.x - s.x) / 2;
                const textY = s.y + (t.y - s.y) / 2 - 5;
                if (isFinite(textX) && isFinite(textY)) {
                  ctx.font = '8px Sans-Serif';
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                  const textWidth = ctx.measureText(link.relationship).width;
                  ctx.fillRect(textX - textWidth / 2 - 2, textY - 6, textWidth + 4, 12);
                  ctx.fillStyle = '#333';
                  ctx.fillText(link.relationship, textX, textY);
                }
              }
            }
          }}
          linkLabel="relationship"
          linkColor="color"
          onNodeClick={handleNodeClick}
          d3AlphaDecay={0.01}
          d3VelocityDecay={0.4}
          cooldownTicks={300}
          nodeRelSize={6}
          nodeVal={(node: any) => node.size}
          width={undefined}
          height={undefined}
          dagLevelDistance={undefined}
          warmupTicks={0}
          cooldownTime={15000}
          autoPauseRedraw={false}
          enableNodeDrag={true}
          enablePanInteraction={true}
          enableZoomInteraction={true}
        />
      </div>
    </div>
  );
};

export default OntologyVisualization;
