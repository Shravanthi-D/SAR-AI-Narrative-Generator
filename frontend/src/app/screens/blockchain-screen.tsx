import { useState, useEffect } from "react";
import { CheckCircle2, Blocks, ExternalLink, XCircle } from "lucide-react";
import { getSAR, verifySAR, type SARReport, type VerifyResponse } from "../../services/api";

interface BlockchainScreenProps {
  reportId: string | null;
}

export function BlockchainScreen({ reportId }: BlockchainScreenProps) {
  const [report, setReport] = useState<SARReport | null>(null);
  const [verifyResult, setVerifyResult] = useState<VerifyResponse | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState(false);

  useEffect(() => {
    if (!reportId) return;
    getSAR(reportId).then(setReport);
  }, [reportId]);

  const handleVerify = async () => {
    if (!reportId) return;
    setVerifying(true);
    setVerifyError(false);
    setVerifyResult(null);
    const result = await verifySAR(reportId);
    if (result.verified) {
      setVerifyResult(result);
    } else {
      setVerifyError(true);
    }
    setVerifying(false);
  };

  const verificationData = {
    transactionHash: report?.blockchain_hash ?? "0x8a3f7c2b9e1d4a6fbc472e1a8d5f3c9e2b7a4d6f1c8e5a3b9f2d7c4e6a1b8c3d",
    blockNumber:     verifyResult?.block_number  ?? "#18,429,847",
    timestamp:       verifyResult?.timestamp     ?? "2026-02-17 10:15:42 UTC",
    network:         verifyResult?.network       ?? "Ethereum Mainnet",
    gasUsed:         "84,523",
    status:          "Verified",
    confirmations:   verifyResult ? String(verifyResult.confirmations) : "1,247",
  };

  const linkedDocuments = [
    {
      id: report?.case_id ?? "SAR-2026-00421",
      type: "SAR Report",
      hash: report?.blockchain_hash ?? "0x4f8c3a2e9d1b7f5a6c3e8d2b9a1f7c4e5d8b3a6f2c9e1d7b4a8c5f3e2d9b6a1c",
      timestamp: report?.last_modified ?? "2026-02-17 10:15:42",
      status: "Anchored"
    },
    {
      id: "TXN-88421",
      type: "Transaction Record",
      hash: "0x9b2d6f1c8e5a3b9f2d7c4e6a1b8c3d4f8c3a2e9d1b7f5a6c3e8d2b9a1f7c4e5",
      timestamp: "2026-02-17 09:23:18",
      status: "Anchored"
    },
    {
      id: "TXN-88465",
      type: "Transaction Record",
      hash: "0x2e9d1b7f5a6c3e8d2b9a1f7c4e5d8b3a6f2c9e1d7b4a8c5f3e2d9b6a1c4f8c3",
      timestamp: "2026-02-17 09:23:20",
      status: "Anchored"
    },
    {
      id: "AUDIT-00421",
      type: "Audit Trail",
      hash: "0x7f5a6c3e8d2b9a1f7c4e5d8b3a6f2c9e1d7b4a8c5f3e2d9b6a1c4f8c3a2e9d1b",
      timestamp: "2026-02-17 10:15:45",
      status: "Anchored"
    }
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-white mb-1" style={{ fontSize: '22px', fontWeight: 500 }}>
          Blockchain Verification
        </h1>
        <p className="text-[#9CA3AF]" style={{ fontSize: '13px' }}>
          Immutable proof and cryptographic verification for case {report?.case_id ?? "SAR-2026-00421"}
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
              Blockchain Anchored
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" style={{ color: '#10B981' }} strokeWidth={1.5} />
              <span className="text-[#10B981]" style={{ fontSize: '13px', fontWeight: 500 }}>
                Verified on {verificationData.network}
              </span>
            </div>
          </div>
        </div>

        {/* Verification Details Grid */}
        <div className="grid grid-cols-2 gap-6">
          <div>
            <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px', fontWeight: 500 }}>Transaction Hash</div>
            <div className="flex items-center gap-2">
              <div
                className="flex-1 px-3 py-2 font-mono text-white overflow-x-auto"
                style={{ backgroundColor: '#0B1F3A', fontSize: '11px', borderRadius: '2px' }}
              >
                {verificationData.transactionHash}
              </div>
              <button className="p-2 hover:bg-[#0B1F3A] transition-colors" style={{ borderRadius: '2px' }}>
                <ExternalLink className="w-4 h-4 text-[#9CA3AF]" strokeWidth={1.5} />
              </button>
            </div>
          </div>

          <div>
            <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px', fontWeight: 500 }}>Block Number</div>
            <div className="text-white" style={{ fontSize: '14px', fontWeight: 500 }}>{verificationData.blockNumber}</div>
          </div>

          <div>
            <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px', fontWeight: 500 }}>Timestamp</div>
            <div className="text-white" style={{ fontSize: '14px', fontWeight: 500 }}>{verificationData.timestamp}</div>
          </div>

          <div>
            <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px', fontWeight: 500 }}>Network</div>
            <div className="text-white" style={{ fontSize: '14px', fontWeight: 500 }}>{verificationData.network}</div>
          </div>

          <div>
            <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px', fontWeight: 500 }}>Gas Used</div>
            <div className="text-white" style={{ fontSize: '14px', fontWeight: 500 }}>{verificationData.gasUsed}</div>
          </div>

          <div>
            <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px', fontWeight: 500 }}>Confirmations</div>
            <div className="text-white" style={{ fontSize: '14px', fontWeight: 500 }}>{verificationData.confirmations}</div>
          </div>
        </div>

        {/* Verify button */}
        <div className="mt-6 flex items-center gap-3">
          <button
            onClick={handleVerify}
            disabled={verifying || !reportId}
            className="px-4 py-2 text-white hover:opacity-90 transition-opacity disabled:opacity-50"
            style={{ backgroundColor: '#1F4ED8', fontSize: '13px', fontWeight: 500, borderRadius: '2px' }}
          >
            {verifying ? "Verifying…" : "Verify on Chain"}
          </button>
          {verifyResult && (
            <div className="flex items-center gap-2 text-[#10B981]" style={{ fontSize: '12px' }}>
              <CheckCircle2 className="w-4 h-4" strokeWidth={1.5} />
              <span>Verification confirmed — hash integrity intact</span>
            </div>
          )}
          {verifyError && (
            <div className="flex items-center gap-2 text-[#DC2626]" style={{ fontSize: '12px' }}>
              <XCircle className="w-4 h-4" strokeWidth={1.5} />
              <span>Verification failed — hash mismatch detected</span>
            </div>
          )}
        </div>
      </div>

      {/* Linked Documents */}
      <div className="border" style={{
        backgroundColor: '#102A43',
        borderColor: '#1F3A5F',
        borderRadius: '2px'
      }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#1F3A5F' }}>
          <h2 className="text-white" style={{ fontSize: '16px', fontWeight: 500 }}>Anchored Documents</h2>
          <p className="text-[#9CA3AF] mt-1" style={{ fontSize: '12px' }}>
            All documents cryptographically linked to this case
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
                    {doc.hash.substring(0, 20)}...{doc.hash.substring(doc.hash.length - 8)}
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
