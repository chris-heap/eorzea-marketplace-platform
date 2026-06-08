import { useState } from "react";
import ChatPanel from "./components/ChatPanel";
import ArbitrageTable from "./components/ArbitrageTable";
import PriceSearch from "./components/PriceSearch";
import VelocityTable from "./components/VelocityTable";
import "./App.css";

const TABS = [
  { key: "chat", label: "Ask the Market" },
  { key: "arbitrage", label: "Arbitrage" },
  { key: "prices", label: "Price Lookup" },
  { key: "velocity", label: "Top Sellers" },
];

function App() {
  const [activeTab, setActiveTab] = useState("chat");

  return (
    <div className="app">
      <header className="app-header">
        <h1>Eorzea Market Board</h1>
        <p className="subtitle">FFXIV Market Analytics</p>
      </header>

      <nav className="tab-bar">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`tab ${activeTab === tab.key ? "active" : ""}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="content">
        {activeTab === "chat" && <ChatPanel />}
        {activeTab === "arbitrage" && <ArbitrageTable />}
        {activeTab === "prices" && <PriceSearch />}
        {activeTab === "velocity" && <VelocityTable />}
      </main>
    </div>
  );
}

export default App;
