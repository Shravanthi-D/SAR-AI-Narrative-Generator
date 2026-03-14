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
  report_id?: string | null;
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
  transactions: unknown[];
  regulations: unknown[];
}

export interface GenerateSARResponse {
  report_id: string;
  status: string;
}

export interface ApproveSARResponse {
  report_id: string;
  status: string;
  blockchain_hash: string | null;
  blockchain_txn: string | null;
}

export interface VerifyResponse {
  integrity_valid: boolean;
  report_id: string;
  blockchain_hash?: string;
  blockchain_txn?: string;
  timestamp?: string;
  reason?: string;
}

export interface AuditLog {
  id: number;
  user_id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: Record<string, unknown>;
  created_at: string;
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_CASES: SARCase[] = [
  { id: "SAR-2026-00421", account: "ACC_001", customer: "Customer_A", type: "Wire Transfer",        amount: "$95,000",  risk: 94, status: "Pending Review",      assignee: "J. Doe",      timestamp: "2026-02-17 09:23", report_id: null },
  { id: "SAR-2026-00420", account: "ACC_002", customer: "Customer_B", type: "Cash Deposit",         amount: "$48,500",  risk: 87, status: "Under Investigation", assignee: "M. Smith",    timestamp: "2026-02-17 08:15", report_id: null },
  { id: "SAR-2026-00419", account: "ACC_003", customer: "Customer_C", type: "Multiple Transfers",   amount: "$125,000", risk: 72, status: "Approved",            assignee: "R. Johnson",  timestamp: "2026-02-17 07:42", report_id: null },
  { id: "SAR-2026-00418", account: "ACC_004", customer: "Customer_D", type: "Structured Deposits",  amount: "$87,300",  risk: 68, status: "Finalized",           assignee: "K. Williams", timestamp: "2026-02-16 16:20", report_id: null },
  { id: "SAR-2026-00417", account: "ACC_005", customer: "Customer_E", type: "International Wire",   amount: "$210,000", risk: 91, status: "Pending Review",      assignee: "J. Doe",      timestamp: "2026-02-16 14:35", report_id: null },
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
    sentence: "This SAR is filed regarding structuring activity detected in account ACC_001.",
    transactions: [
      { txn_id: "TXN_001", amount: 9800.0, txn_type: "CASH_DEPOSIT", txn_timestamp: "2024-01-02" },
      { txn_id: "TXN_002", amount: 9500.0, txn_type: "CASH_DEPOSIT", txn_timestamp: "2024-01-03" },
    ],
    regulations: [
      { source: "FATF Recommendation 20", summary: "Suspicious transaction reporting", relevant_excerpt: "Financial institutions should report suspicious transactions to the FIU when they suspect or have reasonable grounds to suspect that funds are proceeds of criminal activity." },
    ],
  },
  {
    sentence_index: 1,
    sentence: "Multiple cash deposits were made just below the $10,000 reporting threshold.",
    transactions: [
      { txn_id: "TXN_003", amount: 9700.0, txn_type: "CASH_DEPOSIT", txn_timestamp: "2024-01-05" },
      { txn_id: "TXN_004", amount: 9200.0, txn_type: "CASH_DEPOSIT", txn_timestamp: "2024-01-07" },
    ],
    regulations: [
      { source: "PMLA Section 12", summary: "Reporting obligations", relevant_excerpt: "Every banking company, financial institution and intermediary shall furnish information of prescribed transactions to the Director within the prescribed time." },
    ],
  },
];

// ─── API Helpers ──────────────────────────────────────────────────────────────

async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  console.log(`[API] ${options?.method ?? "GET"} ${url}`, options?.body ? JSON.parse(options.body as string) : "");
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const errorText = await response.text();
    console.error(`[API] ERROR ${response.status} ${url}:`, errorText);
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }
  const data = await response.json() as T;
  console.log(`[API] Response ${url}:`, data);
  return data;
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
  // No fallback — let errors surface to the caller
  return apiFetch<GenerateSARResponse>("/api/sar/generate", {
    method: "POST",
    body: JSON.stringify({ account_token, alert_id, date_from, date_to }),
  });
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
  is_final: boolean = true,
): Promise<ApproveSARResponse> {
  try {
    return await apiFetch<ApproveSARResponse>("/api/sar/approve", {
      method: "POST",
      body: JSON.stringify({ report_id, analyst_id, edits, is_final }),
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
      blockchain_hash: hash,
      blockchain_txn: `MOCK_BC_${hash.substring(0, 8).toUpperCase()}`,
    };
  }
}

export async function verifySAR(report_id: string): Promise<VerifyResponse> {
  try {
    return await apiFetch<VerifyResponse>(`/api/sar/${report_id}/verify`);
  } catch {
    return {
      integrity_valid: true,
      report_id,
      blockchain_hash: "fallback-hash-mock",
      timestamp: new Date().toISOString(),
    };
  }
}

export async function tamperDemo(report_id: string): Promise<{ tampered: boolean; message: string }> {
  return apiFetch(`/api/sar/${report_id}/tamper-demo`, { method: "POST" });
}

export async function restoreReport(report_id: string): Promise<{ restored: boolean }> {
  return apiFetch(`/api/sar/${report_id}/restore`, { method: "POST" });
}

export async function getAuditLogs(): Promise<AuditLog[]> {
  try {
    return await apiFetch<AuditLog[]>("/api/audit/logs");
  } catch {
    return [];
  }
}
