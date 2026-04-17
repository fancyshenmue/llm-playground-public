"use client";

import { useState } from "react";
import { ChevronRight, MessageSquare, Database, Settings, TerminalSquare, Box } from "lucide-react";

type NavItem = {
    name: string;
    href: string;
    isActive?: boolean;
    icon?: React.ReactNode;
};

type Category = {
    title: string;
    items: NavItem[];
};

const navigation: Category[] = [
    {
        title: "Chat Type",
        items: [
            { name: "GraphRAG Active", href: "#", isActive: true, icon: <MessageSquare size={16} /> },
            { name: "Vector Only Search", href: "#", isActive: false, icon: <Database size={16} /> },
            { name: "Vanilla Gemma", href: "#", isActive: false, icon: <TerminalSquare size={16} /> }
        ]
    },
    {
        title: "Production",
        items: [
            { name: "Neo4j Monitor", href: "#", isActive: false, icon: <Box size={16} /> },
            { name: "Async ETL Pipeline", href: "#", isActive: false, icon: <Database size={16} /> },
        ]
    },
    {
        title: "Settings",
        items: [
            { name: "API Configs", href: "#", isActive: false, icon: <Settings size={16} /> }
        ]
    }
];

export default function Sidebar() {
    // Keep track of which categories are open
    const [openCategories, setOpenCategories] = useState<Record<string, boolean>>(
        navigation.reduce((acc, cat) => ({ ...acc, [cat.title]: true }), {})
    );

    const toggleCategory = (title: string) => {
        setOpenCategories(prev => ({ ...prev, [title]: !prev[title] }));
    };

    return (
        <aside className="w-72 hidden md:flex flex-col h-[calc(100vh-4rem)] border-r border-[#1E293B] bg-[var(--color-bg-sidebar)] overflow-y-auto pt-6 px-4 pb-8 sticky top-16 scrollbar-hide">
            
            <nav className="flex-1 space-y-6">
                {navigation.map((category) => (
                    <div key={category.title} className="flex flex-col">
                        
                        {/* Category Header (Accordion Toggle) */}
                        <button 
                            onClick={() => toggleCategory(category.title)}
                            className="flex items-center justify-between w-full text-left font-semibold text-sm text-[var(--color-text-heading)] py-2 group hover:text-white transition-colors"
                        >
                            <span>{category.title}</span>
                            <ChevronRight 
                                size={16} 
                                className={`text-[var(--color-text-muted)] transition-transform duration-200 ${
                                    openCategories[category.title] ? "rotate-90" : ""
                                }`} 
                            />
                        </button>
                        
                        {/* Sub-items list */}
                        <div className={`mt-1 pl-3 space-y-1 border-l border-[#1E293B] ml-[6px] accordion-content ${openCategories[category.title] ? "max-h-96 opacity-100" : "max-h-0 opacity-0"}`}>
                            {category.items.map((item) => (
                                <a
                                    key={item.name}
                                    href={item.href}
                                    className={`flex items-center gap-2 group block py-1.5 px-3 text-sm rounded-md transition-all duration-200
                                        ${item.isActive 
                                            ? "text-[var(--color-accent)] font-medium bg-[rgba(56,189,248,0.1)]" 
                                            : "text-[var(--color-text-body)] hover:text-slate-100 hover:bg-[#1E293B]"
                                        }
                                    `}
                                >
                                    <span className="opacity-70 group-hover:opacity-100 transition-opacity">
                                        {item.icon}
                                    </span>
                                    {item.name}
                                </a>
                            ))}
                        </div>
                    </div>
                ))}
            </nav>
            
        </aside>
    );
}
