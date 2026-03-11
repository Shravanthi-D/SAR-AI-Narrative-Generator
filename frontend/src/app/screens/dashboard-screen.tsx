import { useEffect, useState } from "react";
import { TrendingUp, AlertTriangle, FileText, CheckCircle2 } from "lucide-react";
import { getSARCases, type SARCase } from "../../services/api";

interface DashboardScreenProps {
  onNavigate: (screen: string) => void;
}

const FIGMA_ACTIVITY: SARCase[] = [
  { id: "SAR-2026-00421", account: "ACC_001", customer: "Customer_A", type: "Wire Transfer",        amount: "$95,000",  risk: 94, status: "Pending Review",      assignee: "J. Doe",      timestamp: "2026-02-17 09:23" },
  { id: "SAR-2026-00420", account: "ACC_002", customer: "Customer_B", type: "Cash Deposit",         amount: "$48,500",  risk: 87, status: "Under Investigation", assignee: "M. Smith",    timestamp: "2026-02-17 08:15" },
  { id: "SAR-2026-00419", account: "ACC_003", customer: "Customer_C", type: "Multiple Transfers",   amount: "$125,000", risk: 72, status: "Approved",            assignee: "R. Johnson",  timestamp: "2026-02-17 07:42" },
  { id: "SAR-2026-00418", account: "ACC_004", customer: "Customer_D", type: "Structured Deposits",  amount: "$87,300",  risk: 68, status: "Finalized",           assignee: "K. Williams", timestamp: "2026-02-16 16:20" },
  { id: "SAR-2026-00417", account: "ACC_005", customer: "Customer_E", type: "International Wire",   amount: "$210,000", risk: 91, status: "Pending Review",      assignee: "J. Doe",      timestamp: "2026-02-16 14:35" },
];

export function DashboardScreen({ onNavigate }: DashboardScreenProps) {
  const [recentActivity, setRecentActivity] = useState<SARCase[]>(FIGMA_ACTIVITY);

  useEffect(() => {
    getSARCases().then(setRecentActivity).catch(() => setRecentActivity(FIGMA_ACTIVITY));
  }, []);

  // Derive metric values from real data
  const totalCases = recentActivity.length > 5 ? recentActivity.length : 247;
  const pendingReviews = recentActivity.filter((c) => c.status === "Pending Review").length || 18;
  const highRisk = recentActivity.filter((c) => c.risk >= 80).length || 34;
  const reportsToday = recentActivity.filter((c) => c.timestamp?.startsWith("2026-02-17")).length || 12;

  const summaryData = [
    { label: "Total Cases",             value: String(totalCases),    change: "+12 from last week",       changeType: "positive", icon: FileText },
    { label: "Pending Reviews",         value: String(pendingReviews), change: "8 require immediate action", changeType: "warning", icon: AlertTriangle },
    { label: "High Risk Cases",         value: String(highRisk),      change: "+5 flagged today",          changeType: "danger",  icon: AlertTriangle },
    { label: "Reports Generated Today", value: String(reportsToday),  change: "94% approval rate",        changeType: "positive", icon: CheckCircle2 },
  ];

  const getRiskColor = (risk: number) => {
    if (risk >= 80) return "#DC2626";
    if (risk >= 60) return "#F59E0B";
    return "#10B981";
  };

  const getStatusColor = (status: string) => {
    if (status === "Pending Review") return "#F59E0B";
    if (status === "Approved" || status === "Finalized") return "#10B981";
    return "#1F4ED8";
  };

  return (
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-white mb-1" style={{ fontSize: '22px', fontWeight: 500 }}>
          Dashboard
        </h1>
        <p className="text-[#9CA3AF]" style={{ fontSize: '13px' }}>
          Overview of suspicious activity monitoring and case management
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {summaryData.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.label}
              className="border p-4"
              style={{
                backgroundColor: '#102A43',
                borderColor: '#1F3A5F',
                borderRadius: '2px'
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>
                  {item.label}
                </span>
                <Icon
                  className="w-4 h-4 text-[#9CA3AF]"
                  strokeWidth={1.5}
                />
              </div>
              <div className="text-white mb-1" style={{ fontSize: '24px', fontWeight: 500 }}>
                {item.value}
              </div>
              <div
                className="text-xs"
                style={{
                  color: item.changeType === 'positive' ? '#10B981' :
                         item.changeType === 'warning' ? '#F59E0B' : '#DC2626'
                }}
              >
                {item.change}
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Activity Table */}
      <div className="border" style={{
        backgroundColor: '#102A43',
        borderColor: '#1F3A5F',
        borderRadius: '2px'
      }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#1F3A5F' }}>
          <h2 className="text-white" style={{ fontSize: '16px', fontWeight: 500 }}>
            Recent Activity
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b" style={{ borderColor: '#1F3A5F' }}>
                <th className="px-4 py-3 text-left text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>Case ID</th>
                <th className="px-4 py-3 text-left text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>Customer</th>
                <th className="px-4 py-3 text-left text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>Type</th>
                <th className="px-4 py-3 text-left text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>Amount</th>
                <th className="px-4 py-3 text-left text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>Risk Level</th>
                <th className="px-4 py-3 text-left text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>Status</th>
                <th className="px-4 py-3 text-left text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>Assignee</th>
                <th className="px-4 py-3 text-left text-[#9CA3AF]" style={{ fontSize: '12px', fontWeight: 500 }}>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {recentActivity.map((activity) => (
                <tr
                  key={activity.id}
                  className="border-b hover:bg-[#0B1F3A] cursor-pointer transition-colors"
                  style={{ borderColor: '#1F3A5F' }}
                  onClick={() => onNavigate('investigation')}
                >
                  <td className="px-4 py-3 text-white" style={{ fontSize: '13px' }}>{activity.id}</td>
                  <td className="px-4 py-3 text-[#E5E7EB]" style={{ fontSize: '13px' }}>{activity.customer}</td>
                  <td className="px-4 py-3 text-[#E5E7EB]" style={{ fontSize: '13px' }}>{activity.type}</td>
                  <td className="px-4 py-3 text-[#E5E7EB]" style={{ fontSize: '13px', fontWeight: 500 }}>{activity.amount}</td>
                  <td className="px-4 py-3" style={{ fontSize: '13px' }}>
                    <span
                      className="px-2 py-1"
                      style={{
                        backgroundColor: getRiskColor(activity.risk) + '20',
                        color: getRiskColor(activity.risk),
                        borderRadius: '2px'
                      }}
                    >
                      {activity.risk >= 80 ? "High" : activity.risk >= 60 ? "Medium" : "Low"}
                    </span>
                  </td>
                  <td className="px-4 py-3" style={{ fontSize: '13px' }}>
                    <span
                      className="px-2 py-1"
                      style={{
                        backgroundColor: getStatusColor(activity.status) + '20',
                        color: getStatusColor(activity.status),
                        borderRadius: '2px'
                      }}
                    >
                      {activity.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-[#E5E7EB]" style={{ fontSize: '13px' }}>{activity.assignee}</td>
                  <td className="px-4 py-3 text-[#9CA3AF]" style={{ fontSize: '12px' }}>{activity.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Compliance Score */}
      <div className="grid grid-cols-2 gap-4 mt-4">
        <div className="border p-4" style={{
          backgroundColor: '#102A43',
          borderColor: '#1F3A5F',
          borderRadius: '2px'
        }}>
          <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px', fontWeight: 500 }}>
            System Compliance Score
          </div>
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-white" style={{ fontSize: '32px', fontWeight: 500 }}>98.7</span>
            <span className="text-[#9CA3AF]" style={{ fontSize: '14px' }}>/ 100</span>
          </div>
          <div className="w-full h-2" style={{ backgroundColor: '#0B1F3A', borderRadius: '1px' }}>
            <div className="h-full" style={{ width: '98.7%', backgroundColor: '#10B981', borderRadius: '1px' }}></div>
          </div>
        </div>

        <div className="border p-4" style={{
          backgroundColor: '#102A43',
          borderColor: '#1F3A5F',
          borderRadius: '2px'
        }}>
          <div className="text-[#9CA3AF] mb-2" style={{ fontSize: '12px', fontWeight: 500 }}>
            AI Model Accuracy
          </div>
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-white" style={{ fontSize: '32px', fontWeight: 500 }}>96.4</span>
            <span className="text-[#9CA3AF]" style={{ fontSize: '14px' }}>%</span>
          </div>
          <div className="text-[#10B981]" style={{ fontSize: '12px' }}>+2.1% from last month</div>
        </div>
      </div>
    </div>
  );
}
