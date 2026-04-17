import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Sidebar from "./components/Sidebar";
import { Search, Sparkles } from "lucide-react";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "GraphRAG Enterprise Docs",
  description: "Enterprise Semantic Knowledge Graph",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans">
        
        {/* Sticky Header Nav */}
        <header className="sticky top-0 z-50 flex h-16 items-center gap-4 border-b border-[#1E293B] bg-[rgba(11,17,32,0.8)] backdrop-blur-md px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-2 text-[var(--color-text-heading)] font-bold text-lg">
                <div className="w-8 h-8 rounded-lg bg-[var(--color-accent)] flex items-center justify-center text-white">
                    <Sparkles size={18} />
                </div>
                <span>TailRAG Docs</span>
            </div>
            
            {/* Mock Search Bar (Tailwind styling) */}
            <div className="ml-auto hidden md:flex items-center">
                <div className="relative group">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4 group-hover:text-[var(--color-accent)] transition-colors" />
                    <input 
                        type="text" 
                        placeholder="Search documentation..."
                        className="pl-10 pr-4 py-1.5 bg-[#0F172A] border border-[#1E293B] rounded-full text-sm text-slate-300 w-64 focus:outline-none focus:border-[var(--color-accent)] focus:ring-1 focus:ring-[var(--color-accent)] transition-all"
                    />
                    <kbd className="absolute right-3 top-1/2 -translate-y-1/2 hidden sm:block text-[10px] text-slate-500 border border-slate-700 bg-slate-800 rounded px-1.5 py-0.5">⌘K</kbd>
                </div>
            </div>
        </header>

        {/* Main Application Flex Wrapper */}
        <div className="flex-1 flex w-full">
            <Sidebar />
            {/* Main Content Area */}
            <div className="flex-1 min-w-0">
                {children}
            </div>
        </div>
        
      </body>
    </html>
  );
}
