import { useState } from "react";
import { Shield, ChevronRight } from "lucide-react";

interface LoginScreenProps {
  onLogin: (analystId: string) => void;
}

export function LoginScreen({ onLogin }: LoginScreenProps) {
  const [employeeId, setEmployeeId] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (employeeId) {
      onLogin(employeeId);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center" style={{
      backgroundColor: '#0B1F3A',
      fontFamily: 'IBM Plex Sans, Inter, sans-serif'
    }}>
      <div className="w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-10">
          <div className="w-16 h-16 mx-auto mb-4 flex items-center justify-center" style={{
            backgroundColor: '#1F4ED8',
            borderRadius: '2px'
          }}>
            <Shield className="w-9 h-9 text-white" strokeWidth={1.5} />
          </div>
          <h1 className="text-white mb-2" style={{ fontSize: '22px', fontWeight: 500 }}>
            SAR Narrative Generator
          </h1>
          <p className="text-[#9CA3AF]" style={{ fontSize: '13px', fontWeight: 400 }}>
            Enterprise Anti-Money Laundering Platform
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <div className="border p-8" style={{
            backgroundColor: '#102A43',
            borderColor: '#1F3A5F',
            borderRadius: '2px'
          }}>
            {/* Employee ID */}
            <div className="mb-6">
              <label className="block text-[#E5E7EB] mb-2" style={{ fontSize: '13px', fontWeight: 500 }}>
                Employee ID
              </label>
              <input
                type="text"
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                placeholder="Enter your employee ID"
                className="w-full px-3 py-2.5 text-white border focus:outline-none focus:border-[#1F4ED8] transition-colors"
                style={{
                  backgroundColor: '#0B1F3A',
                  borderColor: '#1F3A5F',
                  fontSize: '13px',
                  borderRadius: '2px'
                }}
              />
            </div>

            {/* Password */}
            <div className="mb-6">
              <label className="block text-[#E5E7EB] mb-2" style={{ fontSize: '13px', fontWeight: 500 }}>
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full px-3 py-2.5 text-white border focus:outline-none focus:border-[#1F4ED8] transition-colors"
                style={{
                  backgroundColor: '#0B1F3A',
                  borderColor: '#1F3A5F',
                  fontSize: '13px',
                  borderRadius: '2px'
                }}
              />
            </div>

            {/* Login Button */}
            <button
              type="submit"
              className="w-full py-2.5 text-white font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-opacity"
              style={{
                backgroundColor: '#1F4ED8',
                fontSize: '14px',
                borderRadius: '2px'
              }}
            >
              Sign In
              <ChevronRight className="w-4 h-4" strokeWidth={2} />
            </button>

            {/* Security Info */}
            <div className="mt-6 pt-6 border-t" style={{ borderColor: '#1F3A5F' }}>
              <div className="flex items-center justify-center gap-4 text-[#9CA3AF]" style={{ fontSize: '12px' }}>
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5" style={{ backgroundColor: '#10B981', borderRadius: '1px' }}></div>
                  <span>Secure Banking Network</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5" style={{ backgroundColor: '#10B981', borderRadius: '1px' }}></div>
                  <span>End-to-End Encrypted</span>
                </div>
              </div>
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="mt-6 text-center text-[#9CA3AF]" style={{ fontSize: '12px' }}>
          <p>© 2026 SAR AI Compliance System. All rights reserved.</p>
          <p className="mt-1">Version 2.4.1 • Build 20260217</p>
        </div>
      </div>
    </div>
  );
}
