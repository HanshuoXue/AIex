"use client";

import { useState } from "react";
import CandidateForm from "./components/CandidateForm";
import MatchResults from "./components/MatchResults";
import type { Candidate, MatchResult, AllMatchResults } from "../types";

// 根据环境动态选择 API 地址
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://api-alex-12345.azurewebsites.net'
  : 'http://127.0.0.1:8000';

  //https://api-alex-test-1757506758.azurewebsites.net

export default function Home() {
  const [results, setResults] = useState<
    MatchResult[] | AllMatchResults | null
  >(null);
  const [loading, setLoading] = useState(false);

  const handleMatch = async (candidateData: Candidate) => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/match`,
        // 
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(candidateData),
        }
      );

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Match failed:", error);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const handleDetailedMatch = async (candidateData: Candidate) => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/match/detailed`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(candidateData),
        }
      );

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Detailed match failed:", error);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const handleAllMatch = async (candidateData: Candidate) => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/match/all`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(candidateData),
        }
      );

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Full analysis failed:", error);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="h-screen bg-gray-100 flex flex-col">
      <div className="container mx-auto px-4 py-3 flex-1 flex flex-col max-h-screen">
        <div className="text-center mb-3">
          <h1 className="text-xl font-bold text-gray-800 mb-1">
            🎓 New Zealand Study Program Smart Matching System
          </h1>
          <p className="text-xs text-gray-600">
            AI-Powered Personalized Program Recommendation Platform
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-0 overflow-hidden">
          <div className="flex flex-col min-h-0">
            <CandidateForm
              onMatch={handleMatch}
              onDetailedMatch={handleDetailedMatch}
              onAllMatch={handleAllMatch}
              loading={loading}
            />
          </div>

          <div className="flex flex-col min-h-0">
            <MatchResults results={results} loading={loading} />
          </div>
        </div>
      </div>
    </main>
  );
}
