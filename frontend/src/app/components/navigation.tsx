import {
  LayoutDashboard,
  FileSearch,
  FileText,
  History,
  Blocks,
  Settings,
  Shield,
  LogOut
} from "lucide-react";

interface NavigationProps {
  activeScreen: string;
  onNavigate: (screen: string) => void;
  onLogout: () => void;
  analystId?: string;
}

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "investigation", label: "Cases", icon: FileSearch },
  { id: "editor", label: "SAR Reports", icon: FileText },
  { id: "audit", label: "Audit Trail", icon: History },
  { id: "blockchain", label: "Blockchain", icon: Blocks },
  { id: "settings", label: "Settings", icon: Settings }
];

export function Navigation({ activeScreen, onNavigate, onLogout, analystId }: NavigationProps) {
  const initials = analystId ? analystId.substring(0, 2).toUpperCase() : "JD";
  const displayName = analystId ? `Analyst ${analystId}` : "Jane Doe";
  return (
    <div
      className="w-64 h-screen border-r flex flex-col"
      style={{
        backgroundColor: '#102A43',
        borderColor: '#1F3A5F'
      }}
    >
      {/* Logo */}
      <div className="px-4 py-4 border-b" style={{ borderColor: '#1F3A5F' }}>
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 flex items-center justify-center"
            style={{
              backgroundColor: '#1F4ED8',
              borderRadius: '2px'
            }}
          >
            <Shield className="w-5 h-5 text-white" strokeWidth={1.5} />
          </div>
          <div>
            <div className="text-white" style={{ fontSize: '14px', fontWeight: 500 }}>
              SAR AI Compliance
            </div>
            <div className="text-[#9CA3AF]" style={{ fontSize: '11px' }}>
              Enterprise AML
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-3 py-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeScreen === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 mb-1 transition-colors ${
                isActive
                  ? 'text-white'
                  : 'text-[#9CA3AF] hover:text-white hover:bg-[#0B1F3A]'
              }`}
              style={isActive ? {
                backgroundColor: '#1F4ED8',
                borderRadius: '2px'
              } : { borderRadius: '2px' }}
            >
              <Icon className="w-4 h-4" strokeWidth={1.5} />
              <span style={{ fontSize: '13px', fontWeight: isActive ? 500 : 400 }}>
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>

      {/* User Info & Logout */}
      <div className="border-t" style={{ borderColor: '#1F3A5F' }}>
        <div className="px-4 py-3">
          <div className="flex items-center gap-3 mb-3">
            <div
              className="w-8 h-8 flex items-center justify-center text-white"
              style={{
                backgroundColor: '#1F4ED8',
                fontSize: '12px',
                fontWeight: 500,
                borderRadius: '2px'
              }}
            >
              {initials}
            </div>
            <div>
              <div className="text-white" style={{ fontSize: '12px', fontWeight: 500 }}>
                {displayName}
              </div>
              <div className="text-[#9CA3AF]" style={{ fontSize: '11px' }}>
                Senior Analyst
              </div>
            </div>
          </div>

          <button
            onClick={onLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-[#9CA3AF] hover:text-white hover:bg-[#0B1F3A] transition-colors"
            style={{ borderRadius: '2px', fontSize: '12px' }}
          >
            <LogOut className="w-4 h-4" strokeWidth={1.5} />
            <span>Sign Out</span>
          </button>
        </div>

        <div className="px-4 py-3 border-t text-[#9CA3AF]" style={{
          borderColor: '#1F3A5F',
          fontSize: '10px'
        }}>
          <div>Version 2.4.1</div>
          <div className="mt-0.5">Build 20260217</div>
        </div>
      </div>
    </div>
  );
}
