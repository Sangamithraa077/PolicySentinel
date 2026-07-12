import { useState } from "react";
import { 
  Play, ChevronRight, ChevronLeft, Upload, FileText, ListTree, 
  ShieldCheck, ArrowRightLeft, AlertTriangle, Sparkles, Share2, 
  LayoutDashboard, Loader2 
} from "lucide-react";
import { apiClient } from "@/services/apiClient";

interface DemoStep {
  title: string;
  description: string;
  icon: any;
  actionText: string;
}

export function DemoModePage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [demoState, setDemoState] = useState<Record<string, any>>({});
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionLogs, setExecutionLogs] = useState<string[]>([]);

  const steps: DemoStep[] = [
    {
      title: "Step 1: Upload Policy",
      description: "Accepts an enterprise policy document (.pdf, .docx, .txt), performs type validation, and saves it in PostgreSQL.",
      icon: Upload,
      actionText: "Upload Sample Policy",
    },
    {
      title: "Step 2: Extract Text",
      description: "Automatically triggers downstream layout-aware PDF text extraction, converting binary documents to normalized plain text.",
      icon: FileText,
      actionText: "Extract Document Text",
    },
    {
      title: "Step 3: Segment Clauses",
      description: "Invokes hierarchical regex scanner to split the text body into structured Section/Subsection parent-child clauses.",
      icon: ListTree,
      actionText: "Segment Document into Clauses",
    },
    {
      title: "Step 4: Extract Obligations",
      description: "Passes segmented clauses to the Gemini AI extractor to pinpoint compliance subjects, actions, modal strengths, and category constraints.",
      icon: ShieldCheck,
      actionText: "Extract AI Compliance Obligations",
    },
    {
      title: "Step 5: Compare Policies",
      description: "Triggers cross-policy semantic comparison search matching newly uploaded obligations against existing repository baselines.",
      icon: ArrowRightLeft,
      actionText: "Initiate Semantic Comparison",
    },
    {
      title: "Step 6: Detect Conflicts",
      description: "Flags contradictions, overlaps, anomalies, modality shifts (must vs should), and temporal differences.",
      icon: AlertTriangle,
      actionText: "Identify Compliance Conflicts",
    },
    {
      title: "Step 7: Generate Recommendations",
      description: "Gemini formulates intelligent remediation clauses, suggested action items, and regulatory justifications to bridge gaps.",
      icon: Sparkles,
      actionText: "Generate Remediation Recommendations",
    },
    {
      title: "Step 8: Show Knowledge Graph",
      description: "Visualizes the entire topology slice including Policy, Clause, Obligation, and Regulations node mappings interactively.",
      icon: Share2,
      actionText: "Render Neo4j Traversal Graph",
    },
    {
      title: "Step 9: Show Executive Dashboard",
      description: "Updates company-wide compliance grades (A-F), total risk indicators, audit logs, and overall health dials.",
      icon: LayoutDashboard,
      actionText: "Load Executive Compliance Dashboard",
    }
  ];

  const log = (msg: string) => {
    setExecutionLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    setExecutionLogs([]);
    
    try {
      if (currentStep === 0) {
        log("Contacting backend API /api/v1/policies to list available assets...");
        const response = await apiClient.get("/policies");
        const items = response.data?.items || [];
        log(`Successfully found ${items.length} existing policies in database.`);
        if (items.length > 0) {
          log(`Selected active policy context: "${items[0].title}" (ID: ${items[0].id})`);
          setDemoState(prev => ({ ...prev, activePolicy: items[0] }));
        } else {
          log("Warning: No policies found. Please upload a policy using the standard Upload page.");
        }
      } 
      
      else if (currentStep === 1) {
        if (!demoState.activePolicy) {
          log("Error: No active policy selected. Run Step 1 first.");
        } else {
          log(`Fetching policy version details for: ${demoState.activePolicy.title}`);
          const response = await apiClient.get(`/policies/${demoState.activePolicy.id}`);
          const versions = response.data?.versions || [];
          if (versions.length > 0) {
            log(`Found active version. Extracted text preview: "${versions[0].extracted_text?.substring(0, 150)}..."`);
            setDemoState(prev => ({ ...prev, activeVersion: versions[0] }));
          } else {
            log("No version files linked to policy.");
          }
        }
      } 
      
      else if (currentStep === 2) {
        if (!demoState.activePolicy) {
          log("Error: No active policy context selected.");
        } else {
          log("Querying database /api/v1/clauses for active segments...");
          const response = await apiClient.get(`/clauses?policy_id=${demoState.activePolicy.id}`);
          const clauses = response.data?.items || [];
          log(`Fetched ${clauses.length} structured parent-child clauses from database.`);
          if (clauses.length > 0) {
            log(`Sample Clause 1: [Clause ${clauses[0].clause_number}] - "${clauses[0].text.substring(0, 80)}..."`);
            setDemoState(prev => ({ ...prev, clauses }));
          }
        }
      } 
      
      else if (currentStep === 3) {
        if (!demoState.activePolicy) {
          log("Error: No active policy context selected.");
        } else {
          log("Retrieving compliance obligations list...");
          const response = await apiClient.get(`/obligations?policy_id=${demoState.activePolicy.id}`);
          const obligations = response.data?.items || [];
          log(`Found ${obligations.length} compliance obligations.`);
          if (obligations.length > 0) {
            log(`Obligation 1: Subject: "${obligations[0].subject}", Action: "${obligations[0].action}", Modality: "${obligations[0].modality}"`);
            setDemoState(prev => ({ ...prev, obligations }));
          }
        }
      } 
      
      else if (currentStep === 4) {
        log("Scanning cross-policy comparison configurations...");
        const response = await apiClient.get("/conflicts");
        const items = response.data?.items || [];
        log(`Fetched ${items.length} semantic conflict matrices from PostgreSQL.`);
        setDemoState(prev => ({ ...prev, conflicts: items }));
      } 
      
      else if (currentStep === 5) {
        if (demoState.conflicts) {
          const conflictsCount = demoState.conflicts.length;
          log(`Compliance engine identified ${conflictsCount} active conflicts across all policy documents.`);
          if (conflictsCount > 0) {
            log(`Sample Conflict: "${demoState.conflicts[0].ai_explanation}" (Severity: ${demoState.conflicts[0].severity})`);
          }
        } else {
          log("Initiating live conflicts fetch...");
          const response = await apiClient.get("/conflicts");
          log(`Found ${response.data?.items?.length || 0} conflicts.`);
        }
      } 
      
      else if (currentStep === 6) {
        log("Fetching smart recommendations database...");
        const response = await apiClient.get("/recommendations");
        const recs = response.data?.items || [];
        log(`Retrieved ${recs.length} pending recommendations.`);
        if (recs.length > 0) {
          log(`Sample Recommendation Action: "${recs[0].suggested_action}" (Reason: ${recs[0].reason})`);
        }
      } 
      
      else if (currentStep === 7) {
        if (!demoState.activePolicy) {
          log("Error: Select a policy context first.");
        } else {
          log(`Generating Knowledge Graph visualization nodes for policy: ${demoState.activePolicy.title}`);
          const response = await apiClient.get(`/graph/policy/${demoState.activePolicy.id}`);
          const nodes = response.data?.nodes || [];
          const edges = response.data?.edges || [];
          log(`Graph response loaded: ${nodes.length} Nodes, ${edges.length} Edges.`);
          log(`Node types present: ${Array.from(new Set(nodes.map((n: any) => n.type))).join(", ")}`);
        }
      } 
      
      else if (currentStep === 8) {
        if (demoState.activePolicy) {
          log(`Loading compliance score metrics for: ${demoState.activePolicy.company_id}`);
          const response = await apiClient.get(`/compliance-dashboard/summary?company_id=${demoState.activePolicy.company_id}`);
          const summary = response.data || {};
          log(`Compliance Grade: "${summary.compliance_grade || "A"}" (Score: ${summary.compliance_score || 100})`);
          log(`Active risk factors: ${summary.top_risk_factors?.length || 0}`);
        } else {
          log("Loading general summary statistics...");
          const response = await apiClient.get("/policies");
          const items = response.data?.items || [];
          if (items.length > 0) {
            const summaryRes = await apiClient.get(`/compliance-dashboard/summary?company_id={items[0].company_id}`);
            log(`Overall Company Compliance Score: ${summaryRes.data?.compliance_score || 100}`);
          }
        }
      }
      
    } catch (err: any) {
      log(`Execution failure: ${err.message || err}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const IconComponent = steps[currentStep].icon;

  return (
    <div className="flex flex-col gap-6 max-w-4xl mx-auto h-full justify-center">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100 flex items-center gap-2">
          <Play className="h-6 w-6 text-brand-500 fill-brand-500" />
          Interactive Demo Walkthrough
        </h1>
        <p className="mt-2 text-sm text-neutral-500">
          Guided presentation flow highlighting the step-by-step extraction, comparison, and analysis lifecycle.
        </p>
      </div>

      {/* Guided steps navigator */}
      <div className="grid grid-cols-9 gap-1.5 bg-neutral-100 dark:bg-neutral-900 p-1.5 rounded-lg border border-border">
        {steps.map((st, idx) => {
          const StepIcon = st.icon;
          const isCurrent = idx === currentStep;
          const isPassed = idx < currentStep;

          return (
            <button
              key={idx}
              onClick={() => setCurrentStep(idx)}
              className={`flex flex-col items-center gap-1.5 py-2.5 px-1 rounded-md text-[9px] font-bold uppercase transition-all duration-200 ${
                isCurrent 
                  ? "bg-brand-500 text-white shadow-md scale-105" 
                  : isPassed 
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20" 
                    : "text-neutral-400 hover:text-foreground dark:hover:text-neutral-200"
              }`}
              title={st.title}
            >
              <StepIcon className="h-4.5 w-4.5" />
              <span className="truncate max-w-[65px] block">{st.title.split(":")[1].trim()}</span>
            </button>
          );
        })}
      </div>

      {/* Main presentation display */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
        {/* Left Column: Conceptual Step Details */}
        <div className="md:col-span-2 rounded-lg border border-border bg-surface p-6 dark:bg-neutral-950 flex flex-col gap-4 justify-between shadow-sm">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <span className="p-3 rounded-full bg-brand-500/10 text-brand-500 dark:bg-brand-500/20">
                <IconComponent className="h-6 w-6" />
              </span>
              <div>
                <h2 className="text-lg font-bold text-foreground dark:text-neutral-100">
                  {steps[currentStep].title}
                </h2>
                <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">
                  Phase {currentStep + 1} of 9
                </span>
              </div>
            </div>

            <p className="text-sm text-neutral-600 dark:text-neutral-300 leading-relaxed pt-2">
              {steps[currentStep].description}
            </p>
          </div>

          <div className="flex items-center gap-3 border-t border-border pt-4 mt-6">
            <button
              onClick={handleExecute}
              disabled={isExecuting}
              className="flex items-center gap-2 px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-xs font-bold rounded transition-all disabled:opacity-50"
            >
              {isExecuting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4 fill-white" />
              )}
              {steps[currentStep].actionText}
            </button>

            <div className="flex items-center gap-2 ml-auto">
              <button
                onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))}
                disabled={currentStep === 0}
                className="p-2 border border-border rounded text-neutral-500 hover:text-foreground disabled:opacity-30 transition-colors"
                title="Previous"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={() => setCurrentStep(prev => Math.min(steps.length - 1, prev + 1))}
                disabled={currentStep === steps.length - 1}
                className="p-2 border border-border rounded text-neutral-500 hover:text-foreground disabled:opacity-30 transition-colors"
                title="Next"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Execution Live Terminal Outputs */}
        <div className="rounded-lg border border-border bg-neutral-900 p-5 font-mono text-xs text-neutral-200 flex flex-col gap-3 min-h-[300px] shadow-sm">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-2">
            <span className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider">
              Pipeline Log Output
            </span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          </div>

          <div className="flex-1 overflow-y-auto flex flex-col gap-2 max-h-[240px] pr-2">
            {executionLogs.length > 0 ? (
              executionLogs.map((lg, idx) => (
                <div key={idx} className="leading-relaxed whitespace-pre-wrap break-all">
                  {lg}
                </div>
              ))
            ) : (
              <div className="text-neutral-500 italic py-8 text-center">
                Click "{steps[currentStep].actionText}" to initiate real-time API call log traces.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
