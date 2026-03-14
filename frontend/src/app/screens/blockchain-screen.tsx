import { useState, useEffect } from "react";
import { CheckCircle2, Blocks, ExternalLink, XCircle, AlertTriangle } from "lucide-react";
import { getSAR, verifySAR, tamperDemo, restoreReport, getSARCases, type SARReport, type VerifyResponse } from "../../services/api";

interface BlockchainScreenProps {
  reportId: string | null;
}

export function BlockchainScreen({ reportId: propReportId }: BlockchainScreenProps) {
  const [reportId, setReportId] = useState<string | null>(propReportId);
  const [report, setReport] = useState<SARReport | null>(null);
  const [verifyResult, setVerifyResult] = useState<VerifyResponse | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [tampering, setTampering] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [tamperMessage, setTamperMessage] = useState<string | null>(null);

  // If no reportId passed, find most recently approved case
  useEffect(() => {
    if (propReportId) {
      setReportId(propReportId);
      return;
    }
    getSARCases().then((cases) => {
      const withReport = cases.find((c) => c.report_id);
      if (withReport?.report_id) setReportId(withReport.report_id);
    }).catch(() => {});
  }, [propReportId]);

  useEffect(() => {
    if (!reportId) return;
    getSAR(reportId).then(setReport).catch(() => {});
  }, [reportId]);

  const handleVerify = async () => {
    if (!reportId) return;
    setVerifying(true);
    setVerifyResult(null);
    try {
      const result = await verifySAR(reportId);
      setVerifyResult(result);
    } finally {
      setVerifying(false);
    }
  };

  const handleTamperDemo = async () => {
    if (!reportId) return;
    setTampering(true);
    setVerifyResult(null);
    try {
      const result = await tamperDemo(reportId);
      setTamperMessage(result.message);
      // Refresh report
      const updated = await getSAR(reportId);
      setReport(updated);
    } finally {
      setTampering(false);
    }
  };

  const handleRestore = async () => {
    if (!reportId) return;
    setRestoring(true);
    setTamperMessage(null);
    setVerifyResult(null);
    try {
      await restoreReport(reportId);
      const updated = await getSAR(reportId);
      setReport(updated);
    } finally {
      setRestoring(false);
    }
  };

  const hashDisplay = report?.blockchain_hash
    ?? "0x8a3f7c2b9e1d4a6fbc472e1a8d5f3c9e2b7a4d6f1c8e5a3b9f2d7c4e6a1b8c3d";

  const linkedDocuments = [
    {
      id: report?.case_id ?? "SAR-2026-00421",
      type: "SAR Report",
      hash: report?.blockchain_hash ?? "pending-anchor",
      timestamp: report?.last_modified ?? "—",
      status: report?.blockchain_hash ? "Anchored" : "Pending",
    },
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-white mb-1" style={{ fontSize: '22px', fontWeight: 500 }}>
          Blockchain Verification
        </h1>
        <p className="text-[#9CA3AF]" style={{ fontSize: '13px' }}>
          Immutable proof and cryptographic verification for case {report?.case_id ?? (reportId ?? "SAR-2026-00421")}
        </p>
      </div>

      {/* Main Verification Card */}
      <div className="border p-6 mb-4" style={{
        backgroundColor: '#102A43',
        borderColor: '#1F3A5F',
        borderRadius: '2px'
      }}>
        <div className="flex items-center gap-3 mb-6">
          <div
            className="w-12 h-12 flex items-center justify-center"
            style={{ backgroundColor: '#7C3AED', borderRadius: '2px' }}
          >
            <Blocks className="w-6 h-6 text-white" strokeWidth={1.5} />
          </div>
          <div>
            <div className="text-white mb-1" style={{ fontSize: '18px', fontWeight: 500 }}>
              {report?.blockchain_hash ? "Blockchain Anchored" : "Pending Anchor"}
            </div>
            {report?.blockchain_hash && (
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" style={{ color: '#10B981' }} strokeWidth={1.5} />
                <span className="text-[#10B981]" style={{ fontSize: '13px', fontWeight: 500 }}>
                  SHA-256 hash stored on mock blockchain
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Hash display */}
        <div className="mb-6">
          <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px', fontWeight: 500 }}>
            Document Hash (SHA-256)
          </div>
          <div className="flex items-center gap-2">
            <div
              className="flex-1 px-3 py-2 font-mono text-white overflow-x-auto"
              style={{ backgroundColor: '#0B1F3A', fontSize: '11px', borderRadius: '2px' }}
            >
              {hashDisplay}
            </div>
            <button className="p-2 hover:bg-[#0B1F3A] transition-colors" style={{ borderRadius: '2px' }}>
              <ExternalLink className="w-4 h-4 text-[#9CA3AF]" strokeWidth={1.5} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6 mb-6">
          <div>
            <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px', fontWeight: 500 }}>Blockchain TXN ID</div>
            <div className="text-white font-mono" style={{ fontSize: '12px', fontWeight: 500 }}>
              {report?.blockchain_txn ?? "—"}
            </div>
          </div>
          <div>
            <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px', fontWeight: 500 }}>Anchored At</div>
            <div className="text-white" style={{ fontSize: '14px', fontWeight: 500 }}>
              {report?.last_modified ?? "—"}
            </div>
          </div>
          <div>
            <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px', fontWeight: 500 }}>Mode</div>
            <div className="text-white" style={{ fontSize: '14px', fontWeight: 500 }}>Mock Blockchain</div>
          </div>
          <div>
            <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px', fontWeight: 500 }}>Algorithm</div>
            <div className="text-white" style={{ fontSize: '14px', fontWeight: 500 }}>SHA-256</div>
          </div>
        </div>

        {/* Verify button + result */}
        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={handleVerify}
            disabled={verifying || !reportId}
            className="px-4 py-2 text-white hover:opacity-90 transition-opacity disabled:opacity-50"
            style={{ backgroundColor: '#1F4ED8', fontSize: '13px', fontWeight: 500, borderRadius: '2px' }}
          >
            {verifying ? "Verifying…" : "Verify Integrity"}
          </button>
          {verifyResult && verifyResult.integrity_valid && (
            <div className="flex items-center gap-2 text-[#10B981]" style={{ fontSize: '12px' }}>
              <CheckCircle2 className="w-4 h-4" strokeWidth={1.5} />
              <span>✓ Document integrity confirmed. Hash matches blockchain record.</span>
            </div>
          )}
          {verifyResult && !verifyResult.integrity_valid && (
            <div className="flex items-center gap-2 text-[#DC2626]" style={{ fontSize: '12px' }}>
              <XCircle className="w-4 h-4" strokeWidth={1.5} />
              <span>✗ INTEGRITY VIOLATION — document was altered after approval.</span>
            </div>
          )}
        </div>
      </div>

      {/* Tamper Demo Section */}
      <div className="border p-6 mb-4" style={{
        backgroundColor: '#102A43',
        borderColor: '#F59E0B',
        borderRadius: '2px'
      }}>
        <div className="flex items-center gap-2 mb-3">
          <AlertTriangle className="w-5 h-5" style={{ color: '#F59E0B' }} strokeWidth={1.5} />
          <div className="text-white" style={{ fontSize: '14px', fontWeight: 500 }}>
            Tamper Detection Demo
          </div>
        </div>
        <p className="text-[#9CA3AF] mb-4" style={{ fontSize: '12px' }}>
          Demonstrates how the system detects document tampering. Click "Tamper Document" to
          modify the stored content without updating the blockchain hash, then click "Verify Integrity"
          above to see the violation detected.
        </p>
        <div className="flex gap-3">
          <button
            onClick={handleTamperDemo}
            disabled={tampering || !reportId}
            className="px-4 py-2 text-white hover:opacity-90 transition-opacity disabled:opacity-50"
            style={{ backgroundColor: '#F59E0B', fontSize: '13px', fontWeight: 500, borderRadius: '2px' }}
          >
            {tampering ? "Tampering…" : "Tamper Document"}
          </button>
          <button
            onClick={handleRestore}
            disabled={restoring || !reportId}
            className="px-4 py-2 text-white hover:opacity-90 transition-opacity disabled:opacity-50"
            style={{ backgroundColor: '#10B981', fontSize: '13px', fontWeight: 500, borderRadius: '2px' }}
          >
            {restoring ? "Restoring…" : "Restore Document"}
          </button>
        </div>
        {tamperMessage && (
          <div className="mt-3 px-3 py-2 border border-[#F59E0B]" style={{
            backgroundColor: '#F59E0B20',
            borderRadius: '2px',
            fontSize: '12px',
            color: '#F59E0B'
          }}>
            {tamperMessage}
          </div>
        )}
      </div>

      {/* Anchored Documents */}
      <div className="border" style={{
        backgroundColor: '#102A43',
        borderColor: '#1F3A5F',
        borderRadius: '2px'
      }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#1F3A5F' }}>
          <h2 className="text-white" style={{ fontSize: '16px', fontWeight: 500 }}>Anchored Documents</h2>
          <p className="text-[#9CA3AF] mt-1" style={{ fontSize: '12px' }}>
            Documents cryptographically anchored for this case
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b" style={{ borderColor: '#1F3A5F' }}>
                <th className="px-4 py-3 text-left text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>Document ID</th>
                <th className="px-4 py-3 text-left text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>Type</th>
                <th className="px-4 py-3 text-left text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>Document Hash</th>
                <th className="px-4 py-3 text-left text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>Anchored At</th>
                <th className="px-4 py-3 text-left text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {linkedDocuments.map((doc, index) => (
                <tr
                  key={index}
                  className="border-b hover:bg-[#0B1F3A] transition-colors"
                  style={{ borderColor: '#1F3A5F' }}
                >
                  <td className="px-4 py-3 text-white" style={{ fontSize: '13px', fontWeight: 500 }}>{doc.id}</td>
                  <td className="px-4 py-3 text-[#E5E7EB]" style={{ fontSize: '13px' }}>{doc.type}</td>
                  <td className="px-4 py-3 text-[#9CA3AF] font-mono" style={{ fontSize: '11px' }}>
                    {doc.hash.length > 28
                      ? `${doc.hash.substring(0, 20)}...${doc.hash.substring(doc.hash.length - 8)}`
                      : doc.hash}
                  </td>
                  <td className="px-4 py-3 text-[#9CA3AF]" style={{ fontSize: '12px' }}>{doc.timestamp}</td>
                  <td className="px-4 py-3" style={{ fontSize: '12px' }}>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5" style={{ color: '#10B981' }} strokeWidth={1.5} />
                      <span style={{ color: '#10B981' }}>{doc.status}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Security Features */}
      <div className="grid grid-cols-3 gap-4 mt-4">
        <SecurityCard title="Immutable Record"    description="Once anchored, the data cannot be altered or deleted" icon="🔒" />
        <SecurityCard title="Cryptographic Proof" description="SHA-256 hashing ensures data integrity verification"   icon="🔐" />
        <SecurityCard title="Distributed Ledger"  description="Stored across thousands of nodes for redundancy"       icon="🌐" />
      </div>
    </div>
  );
}

function SecurityCard({ title, description, icon }: { title: string; description: string; icon: string }) {
  return (
    <div className="border p-4" style={{
      backgroundColor: '#102A43',
      borderColor: '#1F3A5F',
      borderRadius: '2px'
    }}>
      <div className="text-2xl mb-3">{icon}</div>
      <div className="text-white mb-2" style={{ fontSize: '13px', fontWeight: 500 }}>{title}</div>
      <div className="text-[#9CA3AF]" style={{ fontSize: '12px' }}>{description}</div>
    </div>
  );
}
