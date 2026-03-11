import { useState, useEffect } from "react";
import { getSARLineage, type LineageEntry } from "../../services/api";

interface EvidencePanelProps {
  reportId: string | null;
}

export function EvidencePanel({ reportId }: EvidencePanelProps) {
  const [lineage, setLineage] = useState<LineageEntry[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!reportId) return;
    setLoading(true);
    getSARLineage(reportId)
      .then((data) => {
        setLineage(data);
        setSelectedIndex(0);
      })
      .finally(() => setLoading(false));
  }, [reportId]);

  if (!reportId) {
    return (
      <p className="text-[#9CA3AF]" style={{ fontSize: '12px' }}>
        No report selected. Generate a SAR from Cases first.
      </p>
    );
  }

  if (loading) {
    return <p className="text-[#9CA3AF]" style={{ fontSize: '12px' }}>Loading lineage…</p>;
  }

  const entry = lineage.find((e) => e.sentence_index === selectedIndex) ?? lineage[0];
  const maxIndex = lineage.length > 0 ? lineage.length - 1 : 0;

  return (
    <div>
      <div className="text-white mb-2" style={{ fontSize: '13px', fontWeight: 500 }}>
        Evidence & Lineage
      </div>
      <p className="text-[#9CA3AF] mb-4" style={{ fontSize: '11px' }}>
        Trace each sentence to its source transactions and regulations.
      </p>

      {/* Sentence selector */}
      <div className="mb-3">
        <label className="block text-[#9CA3AF] mb-1" style={{ fontSize: '11px', fontWeight: 500 }}>
          Sentence Index (0–{maxIndex})
        </label>
        <input
          type="number"
          min={0}
          max={maxIndex}
          value={selectedIndex}
          onChange={(e) => setSelectedIndex(Math.min(maxIndex, Math.max(0, Number(e.target.value))))}
          className="w-full px-2 py-1 text-white border focus:outline-none focus:border-[#1F4ED8] transition-colors"
          style={{
            backgroundColor: '#0B1F3A',
            borderColor: '#1F3A5F',
            fontSize: '12px',
            borderRadius: '2px'
          }}
        />
      </div>

      {/* Selected sentence */}
      {entry && (
        <>
          <div className="border p-3 mb-3" style={{
            backgroundColor: '#0B1F3A',
            borderColor: '#1F3A5F',
            borderRadius: '2px'
          }}>
            <div className="text-[#9CA3AF] mb-1" style={{ fontSize: '10px', fontWeight: 500 }}>SENTENCE</div>
            <p className="text-[#E5E7EB]" style={{ fontSize: '12px', lineHeight: '1.6', fontStyle: 'italic' }}>
              "{entry.sentence}"
            </p>
          </div>

          {/* Transactions */}
          {entry.transactions.length > 0 && (
            <div className="mb-3">
              <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '11px', fontWeight: 500 }}>
                SUPPORTING TRANSACTIONS ({entry.transactions.length})
              </div>
              <div className="border" style={{
                backgroundColor: '#0B1F3A',
                borderColor: '#1F3A5F',
                borderRadius: '2px',
                padding: '8px',
                fontSize: '11px',
                fontFamily: 'monospace',
                color: '#E5E7EB',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all'
              }}>
                {JSON.stringify(entry.transactions, null, 2)}
              </div>
            </div>
          )}

          {/* Regulations */}
          {entry.regulations.length > 0 && (
            <div>
              <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '11px', fontWeight: 500 }}>
                REGULATORY CITATIONS ({entry.regulations.length})
              </div>
              <div className="space-y-2">
                {entry.regulations.map((reg) => (
                  <div
                    key={reg.id}
                    className="p-3"
                    style={{
                      backgroundColor: '#0B1F3A',
                      borderLeft: '3px solid #7C3AED',
                      borderTop: '1px solid #1F3A5F',
                      borderRight: '1px solid #1F3A5F',
                      borderBottom: '1px solid #1F3A5F',
                      borderRadius: '2px'
                    }}
                  >
                    <div className="text-white mb-1" style={{ fontSize: '12px', fontWeight: 500 }}>
                      {reg.title}
                    </div>
                    <div className="text-[#9CA3AF]" style={{ fontSize: '11px', lineHeight: '1.5' }}>
                      {reg.excerpt}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
