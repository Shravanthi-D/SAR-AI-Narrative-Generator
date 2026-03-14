import { useState, useEffect, useRef } from "react";
import { Info, ExternalLink, Network, BookOpen, History, Blocks, CheckCircle2 } from "lucide-react";
import { getSARCases, generateSAR, type SARCase } from "../../services/api";

interface Citation {
  id: string;
  type: "data" | "regulation";
  text: string;
  confidence: number;
  details: string;
}

const citations: Record<string, Citation> = {
  "TXN_88421": {
    id: "TXN_88421",
    type: "data",
    text: "Transaction #TXN_88421",
    confidence: 97,
    details: "Wire transfer of $95,000 from Customer_A to offshore entity XYZ Holdings Ltd. on 2026-02-12"
  },
  "TXN_88465": {
    id: "TXN_88465",
    type: "data",
    text: "Transaction #TXN_88465",
    confidence: 94,
    details: "Cash deposit of $48,500 structured across multiple branches on 2026-02-14"
  },
  "FATF_20": {
    id: "FATF_20",
    type: "regulation",
    text: "FATF Recommendation 20",
    confidence: 99,
    details: "Financial institutions should report suspicious transactions to the FIU when they suspect or have reasonable grounds to suspect that funds are proceeds of criminal activity."
  },
  "PMLA_12": {
    id: "PMLA_12",
    type: "regulation",
    text: "PMLA Section 12",
    confidence: 98,
    details: "Every banking company, financial institution and intermediary shall furnish information of prescribed transactions to the Director within the prescribed time."
  },
  "BSA_314": {
    id: "BSA_314",
    type: "regulation",
    text: "BSA Section 314(a)",
    confidence: 96,
    details: "Requires financial institutions to search their records for accounts and transactions upon request from law enforcement."
  }
};

const FIGMA_CASES = [
  { id: "SAR-2026-00421", account: "ACC_001", customer: "Customer_A", risk: 94, status: "Pending Review",      type: "Wire Transfer",       amount: "$95,000",  assignee: "J. Doe",   timestamp: "" },
  { id: "SAR-2026-00420", account: "ACC_002", customer: "Customer_B", risk: 87, status: "Under Investigation", type: "Cash Deposit",        amount: "$48,500",  assignee: "M. Smith", timestamp: "" },
  { id: "SAR-2026-00419", account: "ACC_003", customer: "Customer_C", risk: 72, status: "Approved",            type: "Multiple Transfers",  amount: "$125,000", assignee: "R. J.",    timestamp: "" },
  { id: "SAR-2026-00418", account: "ACC_004", customer: "Customer_D", risk: 68, status: "Finalized",           type: "Structured Deposits", amount: "$87,300",  assignee: "K. W.",    timestamp: "" },
  { id: "SAR-2026-00417", account: "ACC_005", customer: "Customer_E", risk: 91, status: "Pending Review",      type: "International Wire",  amount: "$210,000", assignee: "J. Doe",   timestamp: "" },
];

const PROGRESS_STEPS = [
  "Investigating transaction patterns...",
  "Retrieving applicable regulations...",
  "Composing SAR narrative...",
  "Building lineage map...",
];

interface InvestigationScreenProps {
  onReportReady: (reportId: string) => void;
  analystId: string;
}

export function InvestigationScreen({ onReportReady, analystId }: InvestigationScreenProps) {
  const [cases, setCases] = useState<SARCase[]>(FIGMA_CASES);
  const [selectedCase, setSelectedCase] = useState(FIGMA_CASES[0].id);
  const [activeTab, setActiveTab] = useState<"evidence" | "citations" | "audit" | "blockchain">("evidence");
  const [hoveredCitation, setHoveredCitation] = useState<string | null>(null);

  // Generation overlay state
  const [generating, setGenerating] = useState(false);
  const [progressStep, setProgressStep] = useState(0);
  const [progressDone, setProgressDone] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const generatePromiseRef = useRef<Promise<string> | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    getSARCases().then(setCases).catch(() => setCases(FIGMA_CASES));
  }, []);

  const getRiskColor = (risk: number) => {
    if (risk >= 80) return "#DC2626";
    if (risk >= 60) return "#F59E0B";
    return "#10B981";
  };

  const handleCitationHover = (id: string) => setHoveredCitation(id);

  const handleGenerateSAR = (caseItem: SARCase) => {
    setSelectedCase(caseItem.id);
    setGenerating(true);
    setProgressStep(0);
    setProgressDone(false);
    setGenerateError(null);

    // Fire the real API call immediately (runs in parallel with animation)
    const apiPromise = generateSAR(
      caseItem.account,
      caseItem.id,
      "2024-01-01",
      "2024-01-31",
    ).then((res) => res.report_id);
    generatePromiseRef.current = apiPromise;

    // Animate steps at 1.5s each
    let step = 0;
    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => {
      step += 1;
      setProgressStep(step);
      if (step >= PROGRESS_STEPS.length - 1) {
        clearInterval(intervalRef.current!);
        intervalRef.current = null;
        // Wait for the API to finish, then navigate
        apiPromise
          .then((reportId) => {
            setProgressDone(true);
            setTimeout(() => {
              setGenerating(false);
              onReportReady(reportId);
            }, 400);
          })
          .catch((err: Error) => {
            setGenerating(false);
            setGenerateError(err.message ?? "Generation failed. Please try again.");
          });
      }
    }, 1500);
  };

  return (
    <div className="flex h-full">
      {/* Left Panel - Case List */}
      <div className="w-72 border-r flex flex-col" style={{
        backgroundColor: '#102A43',
        borderColor: '#1F3A5F'
      }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#1F3A5F' }}>
          <h2 className="text-white" style={{ fontSize: '16px', fontWeight: 500 }}>Active Cases</h2>
          <p className="text-[#9CA3AF] mt-1" style={{ fontSize: '12px' }}>
            {cases.length} cases requiring review
          </p>
        </div>

        <div className="flex-1 overflow-y-auto">
          {cases.map((caseItem) => (
            <div
              key={caseItem.id}
              onClick={() => setSelectedCase(caseItem.id)}
              className={`w-full px-4 py-3 border-b text-left transition-colors cursor-pointer ${
                selectedCase === caseItem.id ? 'bg-[#0B1F3A]' : 'hover:bg-[#0B1F3A]'
              }`}
              style={{ borderColor: '#1F3A5F' }}
            >
              <div className="text-white mb-1" style={{ fontSize: '13px', fontWeight: 500 }}>
                {caseItem.id}
              </div>
              <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px' }}>
                {caseItem.customer}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#9CA3AF]" style={{ fontSize: '11px' }}>Risk Score</span>
                <span style={{ fontSize: '11px', fontWeight: 500, color: getRiskColor(caseItem.risk) }}>
                  {caseItem.risk}
                </span>
              </div>
              <div className="w-full h-1 mt-1.5" style={{ backgroundColor: '#0B1F3A', borderRadius: '1px' }}>
                <div
                  className="h-full"
                  style={{
                    width: `${caseItem.risk}%`,
                    backgroundColor: getRiskColor(caseItem.risk),
                    borderRadius: '1px'
                  }}
                ></div>
              </div>
              {/* Generate SAR button per case */}
              <button
                onClick={(e) => { e.stopPropagation(); handleGenerateSAR(caseItem); }}
                className="mt-2 w-full px-2 py-1 text-white hover:opacity-90 transition-opacity"
                style={{
                  backgroundColor: '#1F4ED8',
                  fontSize: '11px',
                  fontWeight: 500,
                  borderRadius: '2px'
                }}
              >
                Generate SAR
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Center Panel - SAR Narrative */}
      <div className="flex-1 flex flex-col relative" style={{ backgroundColor: '#0B1F3A' }}>

        {/* Generation Overlay */}
        {generating && (
          <div
            className="absolute inset-0 z-10 flex flex-col items-center justify-center"
            style={{ backgroundColor: '#0B1F3A' }}
          >
            <div className="border p-8 w-96" style={{
              backgroundColor: '#102A43',
              borderColor: '#1F3A5F',
              borderRadius: '2px'
            }}>
              <div className="text-white mb-2" style={{ fontSize: '16px', fontWeight: 500 }}>
                Generating SAR Report
              </div>
              <div className="text-[#9CA3AF] mb-6" style={{ fontSize: '12px' }}>
                Case: {selectedCase}
              </div>
              <div className="space-y-3">
                {PROGRESS_STEPS.map((step, i) => {
                  const done = i < progressStep;
                  const active = i === progressStep;
                  return (
                    <div key={i} className="flex items-center gap-3">
                      <div
                        className="w-5 h-5 flex items-center justify-center flex-shrink-0"
                        style={{
                          backgroundColor: done ? '#10B981' : active ? '#1F4ED8' : '#1F3A5F',
                          borderRadius: '2px'
                        }}
                      >
                        {done && <CheckCircle2 className="w-3 h-3 text-white" strokeWidth={2} />}
                        {active && (
                          <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
                        )}
                      </div>
                      <span style={{
                        fontSize: '12px',
                        color: done ? '#10B981' : active ? '#E5E7EB' : '#9CA3AF'
                      }}>
                        {step}
                      </span>
                    </div>
                  );
                })}
              </div>
              {progressDone && (
                <div className="mt-4 flex items-center gap-2 text-[#10B981]" style={{ fontSize: '12px' }}>
                  <CheckCircle2 className="w-4 h-4" strokeWidth={1.5} />
                  <span>Complete — opening editor…</span>
                </div>
              )}
              {generateError && (
                <div className="mt-4 p-3 border border-[#DC2626]" style={{
                  backgroundColor: '#DC262620',
                  borderRadius: '2px'
                }}>
                  <div className="text-[#DC2626] mb-1" style={{ fontSize: '12px', fontWeight: 500 }}>
                    Generation Failed
                  </div>
                  <div className="text-[#E5E7EB]" style={{ fontSize: '11px' }}>
                    {generateError}
                  </div>
                  <button
                    onClick={() => { setGenerating(false); setGenerateError(null); }}
                    className="mt-2 px-3 py-1 text-white"
                    style={{ backgroundColor: '#DC2626', fontSize: '11px', borderRadius: '2px' }}
                  >
                    Dismiss
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="px-6 py-4 border-b" style={{ borderColor: '#1F3A5F' }}>
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-white mb-1" style={{ fontSize: '18px', fontWeight: 500 }}>
                AI Generated SAR Narrative
              </h2>
              <p className="text-[#9CA3AF]" style={{ fontSize: '12px' }}>
                Case: {selectedCase} • Generated: 2026-02-17 09:23:45 UTC
              </p>
            </div>
            <div className="px-3 py-1.5" style={{
              backgroundColor: '#F59E0B20',
              color: '#F59E0B',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: '2px'
            }}>
              Under Review
            </div>
          </div>

          <div className="flex gap-2">
            <button
              className="px-4 py-2 text-white transition-opacity hover:opacity-90"
              style={{ backgroundColor: '#10B981', fontSize: '13px', fontWeight: 500, borderRadius: '2px' }}
            >
              Approve
            </button>
            <button
              className="px-4 py-2 text-white transition-opacity hover:opacity-90"
              style={{ backgroundColor: '#1F4ED8', fontSize: '13px', fontWeight: 500, borderRadius: '2px' }}
            >
              Edit
            </button>
            <button
              className="px-4 py-2 text-white transition-opacity hover:opacity-90"
              style={{ backgroundColor: '#DC2626', fontSize: '13px', fontWeight: 500, borderRadius: '2px' }}
            >
              Reject
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="border" style={{
            backgroundColor: '#102A43',
            borderColor: '#1F3A5F',
            borderRadius: '2px'
          }}>
            <div className="p-6 text-[#E5E7EB] leading-relaxed space-y-4" style={{ fontSize: '13px' }}>
              <p>
                This Suspicious Activity Report (SAR) is filed in relation to{' '}
                <CitationTag id="TXN_88421" onHover={handleCitationHover} onLeave={() => setHoveredCitation(null)} />{' '}
                initiated by Customer_A (Customer ID: CUST-2026-4782). The transaction exhibited multiple red flags consistent with potential money laundering activity as defined under{' '}
                <CitationTag id="FATF_20" onHover={handleCitationHover} onLeave={() => setHoveredCitation(null)} />{' '}
                and{' '}
                <CitationTag id="PMLA_12" onHover={handleCitationHover} onLeave={() => setHoveredCitation(null)} />.
              </p>
              <p>
                On 2026-02-12, Customer_A initiated a wire transfer of $95,000 USD to an offshore entity, XYZ Holdings Ltd., registered in the British Virgin Islands. This transaction was flagged by our automated monitoring system due to the high-risk jurisdiction and the lack of apparent business relationship between the parties.
              </p>
              <p>
                Further analysis revealed that two days later, on 2026-02-14, the same customer made multiple cash deposits totaling $48,500 USD across five different branch locations{' '}
                <CitationTag id="TXN_88465" onHover={handleCitationHover} onLeave={() => setHoveredCitation(null)} />.
                Each deposit was structured to remain below the $10,000 reporting threshold, suggesting an attempt to evade Currency Transaction Report (CTR) filing requirements under{' '}
                <CitationTag id="BSA_314" onHover={handleCitationHover} onLeave={() => setHoveredCitation(null)} />.
              </p>
              <p>
                Customer_A has no documented business activities that would justify transactions of this magnitude. Historical account activity shows typical monthly deposits ranging from $2,000 to $5,000, primarily from employment income. The sudden spike in transaction volume and the use of high-risk jurisdictions raise significant concerns regarding the source and legitimacy of these funds.
              </p>
              <p>
                Based on the aforementioned findings, we have determined that this activity warrants filing a Suspicious Activity Report in accordance with applicable anti-money laundering regulations. All supporting documentation, transaction records, and enhanced due diligence materials have been compiled and are available for regulatory review.
              </p>
            </div>
          </div>

          {/* Confidence Score */}
          <div className="mt-4 border p-4" style={{
            backgroundColor: '#102A43',
            borderColor: '#1F3A5F',
            borderRadius: '2px'
          }}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>AI Generation Confidence</span>
              <span className="text-[#10B981]" style={{ fontSize: '13px', fontWeight: 500 }}>96.8%</span>
            </div>
            <div className="w-full h-1.5" style={{ backgroundColor: '#0B1F3A', borderRadius: '1px' }}>
              <div className="h-full" style={{ width: '96.8%', backgroundColor: '#10B981', borderRadius: '1px' }}></div>
            </div>
          </div>
        </div>

        {/* Citation Tooltip */}
        {hoveredCitation && citations[hoveredCitation] && (
          <div
            className="fixed z-50 w-96 border p-4 shadow-xl"
            style={{
              backgroundColor: '#102A43',
              borderColor: '#1F3A5F',
              borderRadius: '2px',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)'
            }}
          >
            <div className="flex items-start gap-3">
              <div
                className="w-8 h-8 flex items-center justify-center flex-shrink-0"
                style={{
                  backgroundColor: citations[hoveredCitation].type === 'data' ? '#1F4ED8' : '#7C3AED',
                  borderRadius: '2px'
                }}
              >
                {citations[hoveredCitation].type === 'data' ? (
                  <Info className="w-4 h-4 text-white" strokeWidth={1.5} />
                ) : (
                  <ExternalLink className="w-4 h-4 text-white" strokeWidth={1.5} />
                )}
              </div>
              <div className="flex-1">
                <div className="text-white mb-1" style={{ fontSize: '13px', fontWeight: 500 }}>
                  {citations[hoveredCitation].text}
                </div>
                <div className="text-[#9CA3AF] mb-3" style={{ fontSize: '12px' }}>
                  {citations[hoveredCitation].details}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#9CA3AF]" style={{ fontSize: '11px' }}>Confidence</span>
                  <span className="text-[#10B981]" style={{ fontSize: '11px', fontWeight: 500 }}>
                    {citations[hoveredCitation].confidence}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Right Panel - Evidence */}
      <div className="w-80 border-l flex flex-col" style={{
        backgroundColor: '#102A43',
        borderColor: '#1F3A5F'
      }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#1F3A5F' }}>
          <h2 className="text-white" style={{ fontSize: '16px', fontWeight: 500 }}>Evidence & Traceability</h2>
        </div>

        {/* Tabs */}
        <div className="flex border-b" style={{ borderColor: '#1F3A5F' }}>
          {([
            { id: 'evidence',   icon: Network,   label: 'Evidence'   },
            { id: 'citations',  icon: BookOpen,  label: 'Citations'  },
            { id: 'audit',      icon: History,   label: 'Audit'      },
            { id: 'blockchain', icon: Blocks,    label: 'Chain'      },
          ] as const).map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 px-3 py-2.5 border-b-2 transition-colors ${
                  activeTab === tab.id ? 'text-white' : 'text-[#9CA3AF] hover:text-white'
                }`}
                style={{
                  borderColor: activeTab === tab.id ? '#1F4ED8' : 'transparent',
                  fontSize: '11px',
                  fontWeight: 500
                }}
              >
                <Icon className="w-3.5 h-3.5 mx-auto mb-1" strokeWidth={1.5} />
                {tab.label}
              </button>
            );
          })}
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'evidence'   && <EvidenceTab />}
          {activeTab === 'citations'  && <CitationsTab />}
          {activeTab === 'audit'      && <AuditTab />}
          {activeTab === 'blockchain' && <BlockchainTab />}
        </div>
      </div>
    </div>
  );
}

function CitationTag({ id, onHover, onLeave }: { id: string; onHover: (id: string) => void; onLeave: () => void }) {
  const citation = citations[id];
  if (!citation) return null;
  const bgColor = citation.type === 'data' ? '#1F4ED8' : '#7C3AED';

  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 cursor-pointer hover:opacity-80 transition-opacity mx-0.5"
      style={{
        backgroundColor: bgColor + '20',
        color: bgColor,
        fontSize: '11px',
        fontWeight: 500,
        borderRadius: '2px'
      }}
      onMouseEnter={() => onHover(id)}
      onMouseLeave={onLeave}
    >
      [{citation.type === 'data' ? 'DATA' : 'REG'}:{id}]
    </span>
  );
}

function EvidenceTab() {
  const evidenceItems = [
    { label: "Wire Transfer Record",    value: "$95,000 USD",    verified: true },
    { label: "Cash Deposit Records",   value: "5 transactions", verified: true },
    { label: "KYC Documentation",      value: "Complete",       verified: true },
    { label: "Enhanced Due Diligence", value: "Completed",      verified: true },
  ];

  return (
    <div className="space-y-2">
      {evidenceItems.map((item, index) => (
        <div
          key={index}
          className="border p-3 flex items-center justify-between"
          style={{ backgroundColor: '#0B1F3A', borderColor: '#1F3A5F', borderRadius: '2px' }}
        >
          <div>
            <div className="text-white mb-0.5" style={{ fontSize: '12px', fontWeight: 500 }}>{item.label}</div>
            <div className="text-[#9CA3AF]" style={{ fontSize: '11px' }}>{item.value}</div>
          </div>
          <CheckCircle2 className="w-4 h-4" style={{ color: '#10B981' }} strokeWidth={1.5} />
        </div>
      ))}
    </div>
  );
}

function CitationsTab() {
  const regulations = [
    { title: "FATF Recommendation 20", desc: "Suspicious transaction reporting" },
    { title: "PMLA Section 12",        desc: "Reporting obligations" },
    { title: "BSA Section 314(a)",     desc: "Information sharing" },
    { title: "FinCEN SAR Filing",      desc: "Electronic filing requirements" },
  ];

  return (
    <div className="space-y-2">
      {regulations.map((reg, index) => (
        <div
          key={index}
          className="border p-3"
          style={{ backgroundColor: '#0B1F3A', borderColor: '#1F3A5F', borderRadius: '2px' }}
        >
          <div className="flex items-start justify-between mb-1">
            <div className="text-white" style={{ fontSize: '12px', fontWeight: 500 }}>{reg.title}</div>
            <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0 ml-2" style={{ color: '#10B981' }} strokeWidth={1.5} />
          </div>
          <div className="text-[#9CA3AF]" style={{ fontSize: '11px' }}>{reg.desc}</div>
        </div>
      ))}
    </div>
  );
}

function AuditTab() {
  const events = [
    { action: "Report Generated",       user: "AI System",     time: "09:23" },
    { action: "Risk Score Calculated",  user: "ML Model v2.4", time: "09:22" },
    { action: "Case Assigned",          user: "J. Doe",        time: "09:20" },
    { action: "EDD Completed",          user: "J. Smith",      time: "16:15" },
  ];

  return (
    <div className="space-y-3">
      {events.map((event, index) => (
        <div key={index} className="relative pl-6">
          <div
            className="absolute left-0 top-1.5 w-2 h-2"
            style={{ backgroundColor: '#1F4ED8', borderRadius: '1px' }}
          ></div>
          <div className="text-white mb-0.5" style={{ fontSize: '12px', fontWeight: 500 }}>{event.action}</div>
          <div className="text-[#9CA3AF]" style={{ fontSize: '11px' }}>{event.user} • {event.time}</div>
        </div>
      ))}
    </div>
  );
}

function BlockchainTab() {
  return (
    <div className="space-y-3">
      <div className="border p-3" style={{
        backgroundColor: '#0B1F3A',
        borderColor: '#1F3A5F',
        borderRadius: '2px'
      }}>
        <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '11px', fontWeight: 500 }}>Transaction Hash</div>
        <div className="text-white font-mono mb-3" style={{ fontSize: '11px' }}>
          0x8a3f7c2b9e1d4a6f...bc8f2e9c21
        </div>
        <div className="text-[#9CA3AF] mb-1" style={{ fontSize: '11px', fontWeight: 500 }}>Block Number</div>
        <div className="text-white mb-3" style={{ fontSize: '12px' }}>#18,429,847</div>
        <div className="flex items-center gap-2 px-2 py-1.5" style={{
          backgroundColor: '#10B98120',
          borderRadius: '2px'
        }}>
          <CheckCircle2 className="w-3.5 h-3.5" style={{ color: '#10B981' }} strokeWidth={1.5} />
          <span className="text-[#10B981]" style={{ fontSize: '11px', fontWeight: 500 }}>
            Verified on Ethereum Mainnet
          </span>
        </div>
      </div>
    </div>
  );
}
