import { useState, useEffect } from "react";
import { CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import { getSAR, approveSAR, type SARReport } from "../../services/api";
import { EvidencePanel } from "../components/EvidencePanel";

interface EditorScreenProps {
  reportId: string | null;
  analystId: string;
}

export function EditorScreen({ reportId, analystId }: EditorScreenProps) {
  const [report, setReport] = useState<SARReport | null>(null);
  const [sections, setSections] = useState({
    section_1_subject: "",
    section_2_activity: "",
    section_3_why_suspicious: "",
    section_4_regulatory_basis: "",
    section_5_evidence: "",
  });
  const [approvalResult, setApprovalResult] = useState<{ hash: string; txn: string } | null>(null);
  const [approving, setApproving] = useState(false);

  useEffect(() => {
    if (!reportId) return;
    getSAR(reportId).then((r) => {
      setReport(r);
      setSections({
        section_1_subject:       r.sections.section_1_subject       ?? "",
        section_2_activity:      r.sections.section_2_activity      ?? "",
        section_3_why_suspicious: r.sections.section_3_why_suspicious ?? "",
        section_4_regulatory_basis: r.sections.section_4_regulatory_basis ?? "",
        section_5_evidence:      r.sections.section_5_evidence      ?? "",
      });
    });
  }, [reportId]);

  const handleApprove = async () => {
    if (!reportId) return;
    setApproving(true);
    const result = await approveSAR(reportId, analystId, sections);
    setApprovalResult({ hash: result.blockchain_hash, txn: result.blockchain_txn });
    setApproving(false);
  };

  const sectionLabels: Array<[keyof typeof sections, string]> = [
    ["section_1_subject",          "Section 1 — Subject & Filing Basis"],
    ["section_2_activity",         "Section 2 — Transaction Activity"],
    ["section_3_why_suspicious",   "Section 3 — Why Suspicious"],
    ["section_4_regulatory_basis", "Section 4 — Regulatory Basis"],
    ["section_5_evidence",         "Section 5 — Evidence & Conclusion"],
  ];

  const displayReport = report ?? {
    case_id: "SAR-2026-00421",
    customer: "Customer_A",
    generated: "2026-02-17 09:23",
    last_modified: "2026-02-17 10:15",
    analyst: "Jane Doe",
    risk_score: 94,
    compliance_confidence: 96.8,
    metrics: {
      "Regulatory Compliance": "99%",
      "Data Accuracy": "97%",
      "Citation Validity": "95%",
      "Language Quality": "94%",
    },
  };

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-white mb-1" style={{ fontSize: '22px', fontWeight: 500 }}>
          SAR Narrative Editor
        </h1>
        <p className="text-[#9CA3AF]" style={{ fontSize: '13px' }}>
          Edit and finalize suspicious activity report • Case: {displayReport.case_id}
        </p>
      </div>

      <div className="flex-1 flex gap-4">
        {/* Editor */}
        <div className="flex-1 flex flex-col">
          <div className="border mb-4" style={{
            backgroundColor: '#102A43',
            borderColor: '#1F3A5F',
            borderRadius: '2px'
          }}>
            <div className="px-4 py-3 border-b flex items-center justify-between" style={{ borderColor: '#1F3A5F' }}>
              <div className="text-white" style={{ fontSize: '14px', fontWeight: 500 }}>
                Document Editor
              </div>
              <div className="flex gap-2">
                <button className="px-3 py-1.5 text-white" style={{
                  backgroundColor: '#1F4ED8',
                  fontSize: '12px',
                  fontWeight: 500,
                  borderRadius: '2px'
                }}>
                  Save Draft
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              {sectionLabels.map(([key, label]) => (
                <div key={key}>
                  <div className="text-[#9CA3AF] mb-1" style={{ fontSize: '11px', fontWeight: 500 }}>
                    {label}
                  </div>
                  <textarea
                    className="w-full p-4 text-[#E5E7EB] border resize-none focus:outline-none focus:border-[#1F4ED8] transition-colors"
                    style={{
                      backgroundColor: '#0B1F3A',
                      borderColor: '#1F3A5F',
                      fontSize: '13px',
                      lineHeight: '1.8',
                      borderRadius: '2px',
                      fontFamily: 'IBM Plex Sans, Inter, sans-serif',
                      height: '110px',
                    }}
                    value={sections[key]}
                    onChange={(e) => setSections((prev) => ({ ...prev, [key]: e.target.value }))}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Blockchain hash result */}
          {approvalResult && (
            <div className="border p-4 mb-4" style={{
              backgroundColor: '#102A43',
              borderColor: '#10B981',
              borderRadius: '2px'
            }}>
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 className="w-4 h-4" style={{ color: '#10B981' }} strokeWidth={1.5} />
                <span className="text-[#10B981]" style={{ fontSize: '13px', fontWeight: 500 }}>
                  Report approved and anchored to blockchain
                </span>
              </div>
              <div className="text-[#9CA3AF] mb-1" style={{ fontSize: '11px', fontWeight: 500 }}>
                BLOCKCHAIN HASH
              </div>
              <div
                className="px-3 py-2 font-mono text-[#E5E7EB] border overflow-x-auto"
                style={{
                  backgroundColor: '#0B1F3A',
                  borderColor: '#1F3A5F',
                  fontSize: '11px',
                  borderRadius: '2px'
                }}
              >
                {approvalResult.hash}
              </div>
              {approvalResult.txn && (
                <>
                  <div className="text-[#9CA3AF] mt-2 mb-1" style={{ fontSize: '11px', fontWeight: 500 }}>
                    TRANSACTION ID
                  </div>
                  <div
                    className="px-3 py-2 font-mono text-[#E5E7EB] border overflow-x-auto"
                    style={{
                      backgroundColor: '#0B1F3A',
                      borderColor: '#1F3A5F',
                      fontSize: '11px',
                      borderRadius: '2px'
                    }}
                  >
                    {approvalResult.txn}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={handleApprove}
              disabled={approving}
              className="flex-1 py-3 text-white font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-60"
              style={{ backgroundColor: '#10B981', fontSize: '14px', borderRadius: '2px' }}
            >
              <CheckCircle2 className="w-4 h-4" strokeWidth={1.5} />
              {approving ? "Approving…" : "Approve & Finalize Report"}
            </button>
            <button
              className="px-6 py-3 text-white font-medium flex items-center gap-2 hover:opacity-90 transition-opacity"
              style={{ backgroundColor: '#F59E0B', fontSize: '14px', borderRadius: '2px' }}
            >
              <AlertTriangle className="w-4 h-4" strokeWidth={1.5} />
              Request Changes
            </button>
            <button
              className="px-6 py-3 text-white font-medium flex items-center gap-2 hover:opacity-90 transition-opacity"
              style={{ backgroundColor: '#DC2626', fontSize: '14px', borderRadius: '2px' }}
            >
              <XCircle className="w-4 h-4" strokeWidth={1.5} />
              Reject Report
            </button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="w-80">
          {/* Compliance Score */}
          <div className="border p-4 mb-4" style={{
            backgroundColor: '#102A43',
            borderColor: '#1F3A5F',
            borderRadius: '2px'
          }}>
            <div className="text-white mb-3" style={{ fontSize: '14px', fontWeight: 500 }}>
              Compliance Confidence
            </div>
            <div className="flex items-baseline gap-2 mb-3">
              <span className="text-white" style={{ fontSize: '32px', fontWeight: 500 }}>
                {displayReport.compliance_confidence}
              </span>
              <span className="text-[#9CA3AF]" style={{ fontSize: '14px' }}>%</span>
            </div>
            <div className="w-full h-2 mb-4" style={{ backgroundColor: '#0B1F3A', borderRadius: '1px' }}>
              <div
                className="h-full"
                style={{
                  width: `${displayReport.compliance_confidence}%`,
                  backgroundColor: '#10B981',
                  borderRadius: '1px'
                }}
              ></div>
            </div>
            <div className="space-y-2">
              {Object.entries(displayReport.metrics).map(([label, value]) => (
                <div key={label} className="flex items-center justify-between">
                  <span className="text-[#9CA3AF]" style={{ fontSize: '11px' }}>{label}</span>
                  <span style={{ fontSize: '11px', fontWeight: 500, color: '#10B981' }}>{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Document Info */}
          <div className="border p-4 mb-4" style={{
            backgroundColor: '#102A43',
            borderColor: '#1F3A5F',
            borderRadius: '2px'
          }}>
            <div className="text-white mb-3" style={{ fontSize: '14px', fontWeight: 500 }}>
              Document Information
            </div>
            <div className="space-y-3">
              {[
                ["Case ID",       displayReport.case_id],
                ["Customer",      displayReport.customer],
                ["Generated",     displayReport.generated],
                ["Last Modified", displayReport.last_modified],
                ["Analyst",       displayReport.analyst],
                ["Risk Score",    `${displayReport.risk_score} (High)`],
              ].map(([label, value]) => (
                <div key={label}>
                  <div className="text-[#9CA3AF] mb-0.5" style={{ fontSize: '11px', fontWeight: 500 }}>{label}</div>
                  <div className="text-white" style={{ fontSize: '12px' }}>{value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Evidence Panel */}
          <div className="border p-4" style={{
            backgroundColor: '#102A43',
            borderColor: '#1F3A5F',
            borderRadius: '2px'
          }}>
            <EvidencePanel reportId={reportId} />
          </div>
        </div>
      </div>
    </div>
  );
}
