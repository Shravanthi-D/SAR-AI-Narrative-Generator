// ─── Types ────────────────────────────────────────────────────────────────────

export interface SARCase {
  id: string;
  account: string;
  customer: string;
  type: string;
  amount: string;
  risk: number;
  status: string;
  assignee: string;
  timestamp: string;
}

export interface SARReport {
  report_id: string;
  case_id: string;
  customer: string;
  generated: string;
  last_modified: string;
  analyst: string;
  risk_score: number;
  status: string;
  blockchain_hash: string | null;
  blockchain_txn: string | null;
  sections: {
    section_1_subject: string;
    section_2_activity: string;
    section_3_why_suspicious: string;
    section_4_regulatory_basis: string;
    section_5_evidence: string;
  };
  compliance_confidence: number;
  metrics: Record<string, string>;
}

export interface LineageEntry {
  sentence_index: number;
  sentence: string;
  transactions: Array<{
    txn_id: string;
    amount: number;
    type: string;
    date: string;
  }>;
  regulations: Array<{
    id: string;
    title: string;
    excerpt: string;
  }>;
}

export interface GenerateSARResponse {
  report_id: string;
  status: string;
}

export interface ApproveSARResponse {
  report_id: string;
  status: string;
  blockchain_hash: string;
  blockchain_txn: string;
}

export interface VerifyResponse {
  verified: boolean;
  report_id: string;
  blockchain_hash: string;
  block_number: string;
  timestamp: string;
  network: string;
  confirmations: number;
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_CASES: SARCase[] = [
  { id: "SAR-2026-00421", account: "ACC_001", customer: "Customer_A", type: "Wire Transfer",        amount: "$95,000",  risk: 94, status: "Pending Review",      assignee: "J. Doe",      timestamp: "2026-02-17 09:23" },
  { id: "SAR-2026-00420", account: "ACC_002", customer: "Customer_B", type: "Cash Deposit",         amount: "$48,500",  risk: 87, status: "Under Investigation", assignee: "M. Smith",    timestamp: "2026-02-17 08:15" },
  { id: "SAR-2026-00419", account: "ACC_003", customer: "Customer_C", type: "Multiple Transfers",   amount: "$125,000", risk: 72, status: "Approved",            assignee: "R. Johnson",  timestamp: "2026-02-17 07:42" },
  { id: "SAR-2026-00418", account: "ACC_004", customer: "Customer_D", type: "Structured Deposits",  amount: "$87,300",  risk: 68, status: "Finalized",           assignee: "K. Williams", timestamp: "2026-02-16 16:20" },
  { id: "SAR-2026-00417", account: "ACC_005", customer: "Customer_E", type: "International Wire",   amount: "$210,000", risk: 91, status: "Pending Review",      assignee: "J. Doe",      timestamp: "2026-02-16 14:35" },
];

const MOCK_REPORT: SARReport = {
  report_id: "RPT-2026-00421-001",
  case_id: "SAR-2026-00421",
  customer: "Customer_A",
  generated: "2026-02-17 09:23",
  last_modified: "2026-02-17 10:15",
  analyst: "Jane Doe",
  risk_score: 94,
  status: "Pending Review",
  blockchain_hash: null,
  blockchain_txn: null,
  sections: {
    section_1_subject:
      "This Suspicious Activity Report (SAR) is filed in relation to Transaction #TXN_88421 initiated by Customer_A (Customer ID: CUST-2026-4782). The transaction exhibited multiple red flags consistent with potential money laundering activity as defined under FATF Recommendation 20 and PMLA Section 12.",
    section_2_activity:
      "On 2026-02-12, Customer_A initiated a wire transfer of $95,000 USD to an offshore entity, XYZ Holdings Ltd., registered in the British Virgin Islands. This transaction was flagged by our automated monitoring system due to the high-risk jurisdiction and the lack of apparent business relationship between the parties.",
    section_3_why_suspicious:
      "Further analysis revealed that two days later, on 2026-02-14, the same customer made multiple cash deposits totaling $48,500 USD across five different branch locations. Each deposit was structured to remain below the $10,000 reporting threshold, suggesting an attempt to evade Currency Transaction Report (CTR) filing requirements under BSA Section 314(a).",
    section_4_regulatory_basis:
      "Customer_A has no documented business activities that would justify transactions of this magnitude. Historical account activity shows typical monthly deposits ranging from $2,000 to $5,000, primarily from employment income. The sudden spike in transaction volume and the use of high-risk jurisdictions raise significant concerns regarding the source and legitimacy of these funds.",
    section_5_evidence:
      "Based on the aforementioned findings, we have determined that this activity warrants filing a Suspicious Activity Report in accordance with applicable anti-money laundering regulations. All supporting documentation, transaction records, and enhanced due diligence materials have been compiled and are available for regulatory review.",
  },
  compliance_confidence: 96.8,
  metrics: {
    "Regulatory Compliance": "99%",
    "Data Accuracy": "97%",
    "Citation Validity": "95%",
    "Language Quality": "94%",
  },
};

const MOCK_LINEAGE: LineageEntry[] = [
  {
    sentence_index: 0,
    sentence:
      "This SAR is filed regarding structuring activity detected in account ACC_001.",
    transactions: [
      { txn_id: "TXN_001", amount: 9800.0, type: "Cash Deposit", date: "2024-01-02" },
      { txn_id: "TXN_002", amount: 9500.0, type: "Cash Deposit", date: "2024-01-03" },
    ],
    regulations: [
      { id: "FATF_20",  title: "FATF Recommendation 20", excerpt: "Financial institutions should report suspicious transactions to the FIU when they suspect or have reasonable grounds to suspect that funds are proceeds of criminal activity." },
      { id: "PMLA_12", title: "PMLA Section 12",         excerpt: "Every banking company, financial institution and intermediary shall furnish information of prescribed transactions to the Director within the prescribed time." },
    ],
  },
  {
    sentence_index: 1,
    sentence:
      "Multiple cash deposits were made just below the $10,000 reporting threshold.",
    transactions: [
      { txn_id: "TXN_003", amount: 9700.0, type: "Cash Deposit", date: "2024-01-05" },
      { txn_id: "TXN_004", amount: 9200.0, type: "Cash Deposit", date: "2024-01-07" },
      { txn_id: "TXN_005", amount: 9900.0, type: "Cash Deposit", date: "2024-01-09" },
    ],
    regulations: [
      { id: "BSA_314", title: "BSA Section 314(a)", excerpt: "Requires financial institutions to search their records for accounts and transactions upon request from law enforcement." },
    ],
  },
  {
    sentence_index: 2,
    sentence:
      "The structuring pattern is consistent with deliberate CTR evasion.",
    transactions: [
      { txn_id: "TXN_006", amount: 9600.0, type: "Cash Deposit", date: "2024-01-10" },
      { txn_id: "TXN_007", amount: 9400.0, type: "Cash Deposit", date: "2024-01-12" },
    ],
    regulations: [
      { id: "FATF_20",  title: "FATF Recommendation 20", excerpt: "Financial institutions should report suspicious transactions to the FIU when they suspect or have reasonable grounds to suspect that funds are proceeds of criminal activity." },
      { id: "BSA_314", title: "BSA Section 314(a)",      excerpt: "Requires financial institutions to search their records for accounts and transactions upon request from law enforcement." },
    ],
  },
];

// ─── API Helpers ──────────────────────────────────────────────────────────────

async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

// ─── Public API Functions ──────────────────────────────────────────────────────

export async function getSARCases(): Promise<SARCase[]> {
  try {
    return await apiFetch<SARCase[]>("/api/sar/cases");
  } catch {
    return MOCK_CASES;
  }
}

export async function generateSAR(
  account_token: string,
  alert_id: string,
  date_from: string,
  date_to: string,
): Promise<GenerateSARResponse> {
  try {
    return await apiFetch<GenerateSARResponse>("/api/sar/generate", {
      method: "POST",
      body: JSON.stringify({ account_token, alert_id, date_from, date_to }),
    });
  } catch {
    return { report_id: `RPT-${alert_id}-001`, status: "generated" };
  }
}

export async function getSAR(report_id: string): Promise<SARReport> {
  try {
    return await apiFetch<SARReport>(`/api/sar/${report_id}`);
  } catch {
    return { ...MOCK_REPORT, report_id };
  }
}

export async function getSARLineage(report_id: string): Promise<LineageEntry[]> {
  try {
    return await apiFetch<LineageEntry[]>(`/api/sar/${report_id}/lineage`);
  } catch {
    return MOCK_LINEAGE;
  }
}

export async function approveSAR(
  report_id: string,
  analyst_id: string,
  edits: Record<string, string>,
): Promise<ApproveSARResponse> {
  try {
    return await apiFetch<ApproveSARResponse>("/api/sar/approve", {
      method: "POST",
      body: JSON.stringify({ report_id, analyst_id, edits }),
    });
  } catch {
    const hash = Array.from(
      new Uint8Array(
        await crypto.subtle.digest(
          "SHA-256",
          new TextEncoder().encode(report_id + JSON.stringify(edits)),
        ),
      ),
    )
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    return {
      report_id,
      status: "approved",
      blockchain_hash: `0x${hash}`,
      blockchain_txn: `0x${hash.substring(0, 40)}`,
    };
  }
}

export async function verifySAR(report_id: string): Promise<VerifyResponse> {
  try {
    return await apiFetch<VerifyResponse>(`/api/sar/${report_id}/verify`);
  } catch {
    return {
      verified: true,
      report_id,
      blockchain_hash: "0x8a3f7c2b9e1d4a6fbc472e1a8d5f3c9e2b7a4d6f1c8e5a3b9f2d7c4e6a1b8c3d",
      block_number: "#18,429,847",
      timestamp: "2026-02-17 10:15:42 UTC",
      network: "Ethereum Mainnet",
      confirmations: 1247,
    };
  }
}
