import { useState, useEffect, useRef } from "react";
import { Loader2, Share2, Search, Info, ZoomIn, ZoomOut, RotateCcw, AlertTriangle, HelpCircle } from "lucide-react";
import { usePolicies } from "@/hooks/usePolicies";
import { apiClient } from "@/services/apiClient";
import { useQuery } from "@tanstack/react-query";

interface GraphNodeData {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
  x?: number;
  y?: number;
  fx?: number;
  fy?: number;
}

interface GraphEdgeData {
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

interface GraphResponseData {
  nodes: GraphNodeData[];
  edges: GraphEdgeData[];
}

interface ImpactAnalysisData {
  connected_obligations: any[];
  related_regulations: any[];
  conflicts: any[];
  recommendations: any[];
  impacted_policies: any[];
}

export function KnowledgeGraphPage() {
  const [selectedPolicyId, setSelectedPolicyId] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedNode, setSelectedNode] = useState<GraphNodeData | null>(null);

  // Zoom / Pan State
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const isDraggingCanvas = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });

  // Dragging individual nodes
  const [draggedNodeId, setDraggedNodeId] = useState<string | null>(null);

  // 1. Fetch policies
  const policiesQuery = usePolicies();
  const policies = policiesQuery.data?.items ?? [];

  // Set default policy
  useEffect(() => {
    if (policies.length > 0 && !selectedPolicyId) {
      setSelectedPolicyId(policies[0].id);
    }
  }, [policies, selectedPolicyId]);

  // 2. Fetch Graph Slice
  const graphQuery = useQuery<GraphResponseData>({
    queryKey: ["policy-graph-slice", selectedPolicyId],
    queryFn: async () => {
      const response = await apiClient.get<GraphResponseData>(`/graph/policy/${selectedPolicyId}`);
      return response.data;
    },
    enabled: Boolean(selectedPolicyId),
  });

  // 3. Fetch Impact Analysis
  const impactQuery = useQuery<ImpactAnalysisData>({
    queryKey: ["policy-impact-analysis", selectedPolicyId],
    queryFn: async () => {
      const response = await apiClient.get<ImpactAnalysisData>(`/graph/policy/${selectedPolicyId}/impact`);
      return response.data;
    },
    enabled: Boolean(selectedPolicyId),
  });

  const [nodes, setNodes] = useState<GraphNodeData[]>([]);
  const [edges, setEdges] = useState<GraphEdgeData[]>([]);

  // Simulation runner on data fetch
  useEffect(() => {
    if (graphQuery.data) {
      // Clone nodes and edges to avoid mutations
      const fetchedNodes = graphQuery.data.nodes.map((n) => ({ ...n }));
      const fetchedEdges = graphQuery.data.edges.map((e) => ({ ...e }));

      // Run Force-Directed Simulation Layout
      const width = 750;
      const height = 450;
      
      // Initialize random positions near center
      fetchedNodes.forEach((n) => {
        n.x = width / 2 + (Math.random() - 0.5) * 150;
        n.y = height / 2 + (Math.random() - 0.5) * 150;
        n.fx = 0;
        n.fy = 0;
      });

      const k = 0.08; // spring constant
      const rep = 1500; // charge constant
      const steps = 70; // iterations

      for (let step = 0; step < steps; step++) {
        // Repulsion force
        for (let i = 0; i < fetchedNodes.length; i++) {
          for (let j = i + 1; j < fetchedNodes.length; j++) {
            const dx = (fetchedNodes[i].x ?? 0) - (fetchedNodes[j].x ?? 0);
            const dy = (fetchedNodes[i].y ?? 0) - (fetchedNodes[j].y ?? 0);
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = rep / (dist * dist);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            fetchedNodes[i].fx = (fetchedNodes[i].fx ?? 0) + fx;
            fetchedNodes[i].fy = (fetchedNodes[i].fy ?? 0) + fy;
            fetchedNodes[j].fx = (fetchedNodes[j].fx ?? 0) - fx;
            fetchedNodes[j].fy = (fetchedNodes[j].fy ?? 0) - fy;
          }
        }

        // Attraction force
        fetchedEdges.forEach((e) => {
          const source = fetchedNodes.find((n) => n.id === e.source);
          const target = fetchedNodes.find((n) => n.id === e.target);
          if (source && target) {
            const dx = (target.x ?? 0) - (source.x ?? 0);
            const dy = (target.y ?? 0) - (source.y ?? 0);
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = k * (dist - 120);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            source.fx = (source.fx ?? 0) + fx;
            source.fy = (source.fy ?? 0) + fy;
            target.fx = (target.fx ?? 0) - fx;
            target.fy = (target.fy ?? 0) - fy;
          }
        });

        // Center gravity
        fetchedNodes.forEach((n) => {
          const dx = width / 2 - (n.x ?? 0);
          const dy = height / 2 - (n.y ?? 0);
          n.fx = (n.fx ?? 0) + dx * 0.01;
          n.fy = (n.fy ?? 0) + dy * 0.01;
        });

        // Apply velocity update
        fetchedNodes.forEach((n) => {
          const limit = 20;
          const vx = Math.max(-limit, Math.min(limit, n.fx ?? 0));
          const vy = Math.max(-limit, Math.min(limit, n.fy ?? 0));
          n.x = (n.x ?? 0) + vx;
          n.y = (n.y ?? 0) + vy;
          n.fx = 0;
          n.fy = 0;
        });
      }

      setNodes(fetchedNodes);
      setEdges(fetchedEdges);
      
      // Auto-select Policy node initially
      const policyNode = fetchedNodes.find((n) => n.type === "Policy");
      if (policyNode) {
        setSelectedNode(policyNode);
      }
    }
  }, [graphQuery.data]);

  // Handle canvas mouse drag/pan
  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    // If clicking a node, don't pan canvas
    if ((e.target as HTMLElement).tagName === "circle") return;
    
    isDraggingCanvas.current = true;
    dragStart.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (isDraggingCanvas.current) {
      setPan({
        x: e.clientX - dragStart.current.x,
        y: e.clientY - dragStart.current.y,
      });
    } else if (draggedNodeId) {
      // Calculate mouse position inside SVG space
      const svg = e.currentTarget;
      const rect = svg.getBoundingClientRect();
      const clientX = e.clientX - rect.left;
      const clientY = e.clientY - rect.top;

      // Adjust for current pan/zoom transformation
      const x = (clientX - pan.x) / zoom;
      const y = (clientY - pan.y) / zoom;

      setNodes((prevNodes) =>
        prevNodes.map((n) => (n.id === draggedNodeId ? { ...n, x, y } : n))
      );
    }
  };

  const handleMouseUp = () => {
    isDraggingCanvas.current = false;
    setDraggedNodeId(null);
  };

  const getNodeColor = (type: string) => {
    switch (type) {
      case "Policy":
        return "#3b82f6"; // blue
      case "Clause":
        return "#14b8a6"; // teal
      case "Obligation":
        return "#f59e0b"; // amber
      case "Regulation":
        return "#a855f7"; // purple
      case "Finding":
        return "#ef4444"; // red
      case "Recommendation":
        return "#10b981"; // emerald
      default:
        return "#737373"; // neutral
    }
  };

  const resetZoomPan = () => {
    setPan({ x: 0, y: 0 });
    setZoom(1);
  };

  const handleNodeClick = (node: GraphNodeData) => {
    setSelectedNode(node);
  };

  const impact = impactQuery.data;

  return (
    <div className="flex flex-col gap-6 h-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100 flex items-center gap-2">
            <Share2 className="h-6 w-6 text-brand-500" />
            Knowledge Graph Explorer
          </h1>
          <p className="mt-2 text-sm text-neutral-500">
            Traverse internal policy structures and external regulatory standard alignments interactively.
          </p>
        </div>

        {/* Policy Selector Dropdown */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-neutral-400">Context:</span>
          <select
            value={selectedPolicyId}
            onChange={(e) => setSelectedPolicyId(e.target.value)}
            className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-brand-500 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900"
          >
            {policies.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Grid View */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        
        {/* Left 3 Columns: Graph visualizer and controls */}
        <div className="lg:col-span-3 flex flex-col gap-4">
          <div className="rounded-lg border border-border bg-surface dark:border-neutral-800 dark:bg-neutral-950 overflow-hidden relative shadow-sm h-[480px]">
            
            {/* Overlay Graph Type Legend */}
            <div className="absolute top-4 left-4 z-10 flex flex-wrap gap-2.5 bg-surface/90 dark:bg-neutral-900/90 p-2.5 rounded-md border border-border dark:border-neutral-800 backdrop-blur-sm text-[10px] font-bold">
              {[
                { label: "Policy", color: "#3b82f6" },
                { label: "Clause", color: "#14b8a6" },
                { label: "Obligation", color: "#f59e0b" },
                { label: "Regulation", color: "#a855f7" },
                { label: "Finding", color: "#ef4444" },
                { label: "Recommendation", color: "#10b981" },
              ].map((lg) => (
                <div key={lg.label} className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: lg.color }} />
                  <span className="text-neutral-600 dark:text-neutral-300 uppercase tracking-wider">{lg.label}</span>
                </div>
              ))}
            </div>

            {/* Navigation controls */}
            <div className="absolute bottom-4 right-4 z-10 flex flex-col gap-1.5 bg-surface/90 dark:bg-neutral-900/90 p-1.5 rounded-md border border-border dark:border-neutral-800 backdrop-blur-sm">
              <button 
                onClick={() => setZoom(z => Math.min(2.5, z + 0.15))}
                className="p-1 text-neutral-400 hover:text-foreground dark:hover:text-white rounded transition-colors"
                title="Zoom In"
              >
                <ZoomIn className="h-4 w-4" />
              </button>
              <button 
                onClick={() => setZoom(z => Math.max(0.4, z - 0.15))}
                className="p-1 text-neutral-400 hover:text-foreground dark:hover:text-white rounded transition-colors"
                title="Zoom Out"
              >
                <ZoomOut className="h-4 w-4" />
              </button>
              <button 
                onClick={resetZoomPan}
                className="p-1 text-neutral-400 hover:text-foreground dark:hover:text-white rounded transition-colors"
                title="Recenter"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
            </div>

            {/* SVG Interactive Canvas */}
            {graphQuery.isLoading ? (
              <div className="w-full h-full flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
              </div>
            ) : (
              <svg
                className="w-full h-full cursor-grab active:cursor-grabbing select-none"
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
              >
                {/* SVG Marker Definitions for Directed Arrowheads */}
                <defs>
                  <marker
                    id="arrowhead"
                    viewBox="0 0 10 10"
                    refX="20"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#737373" opacity="0.4" />
                  </marker>
                </defs>

                <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
                  {/* Edges */}
                  {edges.map((e, idx) => {
                    const sourceNode = nodes.find((n) => n.id === e.source);
                    const targetNode = nodes.find((n) => n.id === e.target);
                    if (!sourceNode || !targetNode) return null;

                    return (
                      <g key={`edge-${idx}`}>
                        <line
                          x1={sourceNode.x}
                          y1={sourceNode.y}
                          x2={targetNode.x}
                          y2={targetNode.y}
                          stroke="#737373"
                          strokeOpacity={0.25}
                          strokeWidth={1.5}
                          markerEnd="url(#arrowhead)"
                        />
                        {/* Text labels on edges */}
                        <text
                          x={((sourceNode.x ?? 0) + (targetNode.x ?? 0)) / 2}
                          y={((sourceNode.y ?? 0) + (targetNode.y ?? 0)) / 2 - 4}
                          fontSize="7"
                          fill="#737373"
                          opacity="0.6"
                          textAnchor="middle"
                          fontWeight="bold"
                        >
                          {e.type}
                        </text>
                      </g>
                    );
                  })}

                  {/* Nodes */}
                  {nodes.map((n) => {
                    const isSelected = selectedNode?.id === n.id;
                    return (
                      <g
                        key={n.id}
                        transform={`translate(${n.x}, ${n.y})`}
                        onClick={() => handleNodeClick(n)}
                        onMouseDown={(e) => {
                          e.stopPropagation();
                          setDraggedNodeId(n.id);
                        }}
                        className="cursor-pointer"
                      >
                        <circle
                          r={isSelected ? 14 : 10}
                          fill={getNodeColor(n.type)}
                          stroke={isSelected ? "#ffffff" : "none"}
                          strokeWidth={isSelected ? 2 : 0}
                          className="transition-all hover:scale-110 shadow-md"
                        />
                        <text
                          y={20}
                          textAnchor="middle"
                          fontSize="9"
                          fontWeight={isSelected ? "bold" : "normal"}
                          fill="currentColor"
                          className="text-neutral-700 dark:text-neutral-300"
                        >
                          {n.label.length > 15 ? `${n.label.substring(0, 15)}...` : n.label}
                        </text>
                      </g>
                    );
                  })}
                </g>
              </svg>
            )}
          </div>

          {/* TRAVERSAL IMPACT ANALYSIS */}
          <div className="rounded-lg border border-border bg-surface p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-4">
            <div>
              <h2 className="text-sm font-bold text-foreground dark:text-neutral-100 uppercase tracking-wider block">
                Policy Traversal Impact Analysis
              </h2>
              <p className="text-xs text-neutral-500 mt-1">
                Visualizes connected graph metrics computed through downstream Neo4j traversal hops.
              </p>
            </div>

            {impactQuery.isLoading ? (
              <Loader2 className="h-6 w-6 animate-spin text-brand-500 mx-auto py-8" />
            ) : impact ? (
              <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
                <div className="rounded-md bg-neutral-50 p-3.5 dark:bg-neutral-900/30 border border-border dark:border-neutral-800">
                  <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Connected Obligations</span>
                  <span className="text-xl font-bold text-neutral-900 dark:text-white mt-1 block">
                    {impact.connected_obligations.length}
                  </span>
                </div>
                <div className="rounded-md bg-neutral-50 p-3.5 dark:bg-neutral-900/30 border border-border dark:border-neutral-800">
                  <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Related Regulations</span>
                  <span className="text-xl font-bold text-neutral-900 dark:text-white mt-1 block">
                    {impact.related_regulations.length}
                  </span>
                </div>
                <div className="rounded-md bg-neutral-50 p-3.5 dark:bg-neutral-900/30 border border-border dark:border-neutral-800">
                  <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Conflicts</span>
                  <span className="text-xl font-bold text-red-600 dark:text-red-400 mt-1 block">
                    {impact.conflicts.length}
                  </span>
                </div>
                <div className="rounded-md bg-neutral-50 p-3.5 dark:bg-neutral-900/30 border border-border dark:border-neutral-800">
                  <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Recommendations</span>
                  <span className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 block">
                    {impact.recommendations.length}
                  </span>
                </div>
                <div className="rounded-md bg-neutral-50 p-3.5 dark:bg-neutral-900/30 border border-border dark:border-neutral-800">
                  <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Impacted Policies</span>
                  <span className="text-xl font-bold text-neutral-900 dark:text-white mt-1 block">
                    {impact.impacted_policies.length}
                  </span>
                </div>
              </div>
            ) : null}
          </div>

        </div>

        {/* Right Column: Node details viewer */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          {selectedNode ? (
            <div className="rounded-lg border border-border bg-surface p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-foreground dark:text-neutral-100 flex items-center gap-1.5">
                  <Info className="h-4 w-4 text-brand-500" />
                  Node Details
                </h3>
                <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[9px] font-bold`} style={{
                  backgroundColor: `${getNodeColor(selectedNode.type)}20`,
                  color: getNodeColor(selectedNode.type)
                }}>
                  {selectedNode.type}
                </span>
              </div>

              <div className="border-t border-border pt-3 flex flex-col gap-4">
                <div className="text-xs">
                  <span className="font-semibold text-neutral-400 uppercase tracking-wider block text-[10px]">Node ID</span>
                  <span className="text-foreground font-mono mt-0.5 block break-all">{selectedNode.id}</span>
                </div>

                <div className="text-xs">
                  <span className="font-semibold text-neutral-400 uppercase tracking-wider block text-[10px]">Title / Label</span>
                  <span className="text-foreground font-semibold mt-0.5 block leading-relaxed">{selectedNode.label}</span>
                </div>

                {/* Print other properties dynamically */}
                {Object.keys(selectedNode.properties).length > 0 && (
                  <div className="flex flex-col gap-2.5 border-t border-border pt-3">
                    <span className="font-semibold text-neutral-400 uppercase tracking-wider block text-[10px]">Properties</span>
                    <div className="flex flex-col gap-2 bg-neutral-50/50 p-2.5 rounded dark:bg-neutral-900/30 border border-border dark:border-neutral-800">
                      {Object.entries(selectedNode.properties).map(([k, v]) => {
                        // Skip printing values that are duplicate to ID or Label
                        if (k === "id" || k === "title" || k === "clause_number" || k === "subject") return null;
                        return (
                          <div key={k} className="text-xs">
                            <span className="font-medium text-neutral-400 uppercase tracking-wider text-[9px]">{k}</span>
                            <span className="text-foreground mt-0.5 block leading-relaxed">{String(v)}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-neutral-300 p-8 text-center text-sm text-neutral-400 dark:border-neutral-800">
              Click on a graph node to explore its attributes and relationship connections.
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
